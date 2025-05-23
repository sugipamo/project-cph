def test_main_import():
    import src.main

def test_main_callable():
    from src import main
    if hasattr(main, "main"):
        main.main() 