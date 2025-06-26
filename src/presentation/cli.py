import click
from pathlib import Path
from typing import List, Optional
import json
import sys

from src.application.use_cases import (
    FindBrokenImportsUseCase,
    FindBrokenImportsRequest,
    SearchImportCandidatesUseCase,
    SearchImportCandidatesRequest,
    FixImportsUseCase,
    FixImportsRequest,
    ImportFix
)
from src.domain.models import BrokenImport


@click.group()
@click.version_option(version='0.1.0', prog_name='import-fixer')
def cli():
    """Automated tool for fixing broken Python imports."""
    pass


@cli.command()
@click.option('--root', '-r', type=click.Path(exists=True, file_okay=False, path_type=Path),
              default='.', help='Project root directory')
@click.option('--file', '-f', type=click.Path(exists=True, dir_okay=False, path_type=Path),
              multiple=True, help='Specific files to check')
@click.option('--exclude', '-e', multiple=True, help='Patterns to exclude')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('--no-circular-check', is_flag=True, help='Skip circular import detection')
def find(root: Path, file: tuple, exclude: tuple, output_json: bool, no_circular_check: bool):
    """Find broken imports in the project."""
    use_case = FindBrokenImportsUseCase()
    
    request = FindBrokenImportsRequest(
        project_root=root,
        target_files=list(file) if file else None,
        exclude_patterns=list(exclude) if exclude else None,
        check_circular_imports=not no_circular_check
    )
    
    response = use_case.execute(request)
    
    # 循環インポートが検出された場合はエラーとして報告
    if response.check_result.has_circular_imports:
        click.echo(click.style("\n✗ CIRCULAR IMPORTS DETECTED!", fg='red', bold=True))
        click.echo(click.style(f"Found {len(response.check_result.circular_imports)} circular import cycles.", fg='red'))
        click.echo("\nCircular import cycles:")
        
        for i, circular in enumerate(response.check_result.circular_imports, 1):
            click.echo(f"\n{i}. {circular}")
            
        click.echo(click.style("\nPlease fix these circular imports manually before proceeding.", fg='yellow'))
        sys.exit(1)
    
    if output_json:
        output = {
            'broken_imports': [
                {
                    'file': str(bi.file_path),
                    'line': bi.line_number,
                    'statement': bi.import_statement,
                    'module': bi.module_path,
                    'error': bi.error_message
                }
                for bi in response.broken_imports
            ],
            'summary': response.metadata,
            'circular_imports': [
                {
                    'cycle': [str(p) for p in ci.cycle_path],
                    'involved_modules': list(ci.involved_modules)
                }
                for ci in response.check_result.circular_imports
            ] if response.check_result.has_circular_imports else []
        }
        click.echo(json.dumps(output, indent=2))
    else:
        if not response.broken_imports:
            click.echo(click.style("✓ No broken imports found!", fg='green'))
            return
        
        click.echo(click.style(f"\nFound {len(response.broken_imports)} broken imports:", fg='yellow'))
        
        current_file = None
        for bi in response.broken_imports:
            if bi.file_path != current_file:
                current_file = bi.file_path
                click.echo(f"\n{click.style(str(bi.file_path), fg='blue', bold=True)}")
            
            click.echo(f"  Line {bi.line_number}: {click.style(bi.import_statement, fg='red')}")
            if bi.error_message:
                click.echo(f"    → {bi.error_message}")


@cli.command()
@click.option('--root', '-r', type=click.Path(exists=True, file_okay=False, path_type=Path),
              default='.', help='Project root directory')
@click.option('--auto', '-a', is_flag=True, help='Automatically fix all broken imports')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--dry-run', is_flag=True, help='Show what would be changed without modifying files')
@click.option('--no-backup', is_flag=True, help='Do not create backup files')
@click.option('--strategy', '-s', multiple=True, 
              type=click.Choice(['symbol_based', 'path_based', 'directory_pattern']),
              help='Search strategies to use (can specify multiple)')
def fix(root: Path, auto: bool, interactive: bool, dry_run: bool, no_backup: bool, strategy: tuple):
    """Fix broken imports in the project."""
    
    find_use_case = FindBrokenImportsUseCase()
    search_use_case = SearchImportCandidatesUseCase()
    fix_use_case = FixImportsUseCase()
    
    click.echo("Scanning for broken imports...")
    find_response = find_use_case.execute(
        FindBrokenImportsRequest(project_root=root)
    )
    
    if not find_response.broken_imports:
        click.echo(click.style("✓ No broken imports found!", fg='green'))
        return
    
    click.echo(f"Found {len(find_response.broken_imports)} broken imports.")
    
    fixes = []
    
    for broken_import in find_response.broken_imports:
        click.echo(f"\n{click.style(str(broken_import), fg='yellow')}")
        
        search_response = search_use_case.execute(
            SearchImportCandidatesRequest(
                broken_import=broken_import,
                project_root=root,
                strategies=list(strategy) if strategy else None
            )
        )
        
        if not search_response.candidates:
            click.echo(click.style("  ✗ No candidates found", fg='red'))
            continue
        
        chosen_candidate = None
        
        if auto:
            chosen_candidate = search_response.candidates[0]
            click.echo(f"  → Auto-selected: {chosen_candidate.module_path}")
        elif interactive:
            click.echo("  Candidates:")
            for i, candidate in enumerate(search_response.candidates[:5], 1):
                score_display = f"{candidate.score.total:.2f}"
                symbols = ', '.join(candidate.matched_symbols) if candidate.matched_symbols else 'N/A'
                click.echo(f"    {i}. {candidate.module_path} (score: {score_display}, symbols: {symbols})")
            
            choice = click.prompt("  Choose candidate (0 to skip)", type=int, default=0)
            if 0 < choice <= len(search_response.candidates[:5]):
                chosen_candidate = search_response.candidates[choice - 1]
        else:
            top_candidate = search_response.candidates[0]
            click.echo(f"  Best match: {top_candidate.module_path} (score: {top_candidate.score.total:.2f})")
            if click.confirm("  Apply this fix?"):
                chosen_candidate = top_candidate
        
        if chosen_candidate:
            new_statement = _generate_import_statement(broken_import, chosen_candidate)
            fixes.append(ImportFix(
                broken_import=broken_import,
                chosen_candidate=chosen_candidate,
                new_import_statement=new_statement
            ))
    
    if not fixes:
        click.echo("\nNo fixes to apply.")
        return
    
    click.echo(f"\n{len(fixes)} fixes ready to apply.")
    
    if dry_run:
        click.echo("\nDry run - no files will be modified:")
        for fix in fixes:
            click.echo(f"\n{fix.broken_import.file_path}:{fix.broken_import.line_number}")
            click.echo(f"  - {fix.broken_import.import_statement}")
            click.echo(f"  + {fix.new_import_statement}")
        return
    
    if not auto and not click.confirm("\nApply fixes?"):
        return
    
    fix_response = fix_use_case.execute(
        FixImportsRequest(
            fixes=fixes,
            dry_run=False,
            backup=not no_backup
        )
    )
    
    click.echo(f"\n✓ Successfully fixed {len(fix_response.successful_fixes)} imports")
    if fix_response.failed_fixes:
        click.echo(f"✗ Failed to fix {len(fix_response.failed_fixes)} imports")
    
    if fix_response.backup_files:
        click.echo(f"\nBackup files created: {len(fix_response.backup_files)}")


def _generate_import_statement(broken_import: BrokenImport, candidate):
    if broken_import.import_type.value == 'import':
        return f"import {candidate.module_path}"
    else:
        names = ', '.join(broken_import.imported_names)
        return f"from {candidate.module_path} import {names}"


@cli.command()
@click.option('--root', '-r', type=click.Path(exists=True, file_okay=False, path_type=Path),
              default='.', help='Project root directory')
def analyze(root: Path):
    """Analyze import health of the project."""
    use_case = FindBrokenImportsUseCase()
    
    response = use_case.execute(
        FindBrokenImportsRequest(project_root=root, check_circular_imports=True)
    )
    
    click.echo(f"\n{click.style('Import Health Report', fg='blue', bold=True)}")
    click.echo(f"{'=' * 40}")
    click.echo(f"Total files scanned: {response.total_files_scanned}")
    click.echo(f"Files with errors: {len(response.files_with_errors)}")
    click.echo(f"Broken imports found: {response.metadata['broken_imports_count']}")
    click.echo(f"Affected files: {response.metadata['affected_files_count']}")
    click.echo(f"Error rate: {response.metadata['error_rate']:.1%}")
    
    # 循環インポートの報告
    if response.check_result.has_circular_imports:
        click.echo(f"\n{click.style('⚠ CIRCULAR IMPORTS DETECTED!', fg='red', bold=True)}")
        click.echo(f"Circular import cycles: {len(response.check_result.circular_imports)}")
        for i, circular in enumerate(response.check_result.circular_imports, 1):
            click.echo(f"\n  Cycle {i}: {circular}")
    
    if response.broken_imports:
        click.echo(f"\n{click.style('Most problematic modules:', fg='yellow')}")
        module_counts = {}
        for bi in response.broken_imports:
            module = bi.module_path or '<relative>'
            module_counts[module] = module_counts.get(module, 0) + 1
        
        for module, count in sorted(module_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            click.echo(f"  {module}: {count} occurrences")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()