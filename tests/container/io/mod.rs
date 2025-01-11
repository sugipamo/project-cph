use cphelper::container::io::buffer::OutputBuffer;
use std::io::Write;

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Duration;

    #[test]
    fn test_output_buffer_write() {
        let mut buffer = OutputBuffer::new();
        let test_data = b"Hello, World!\n";
        
        assert!(buffer.write(test_data).is_ok());
        assert!(buffer.flush().is_ok());
    }

    #[test]
    fn test_output_buffer_read() {
        let mut buffer = OutputBuffer::new();
        let test_data = b"Test Message\n";
        
        buffer.write(test_data).unwrap();
        buffer.flush().unwrap();
        
        let content = buffer.contents();
        assert!(content.contains("Test Message"));
    }

    #[test]
    fn test_buffer_capacity() {
        let buffer = OutputBuffer::new();
        assert!(buffer.capacity() > 0);
    }
} 