from handlers.api_handler.api_handler import APIHandler

def main():
    handler = APIHandler()
    print(handler.handle_request())
if __name__ == '__main__':
    main()