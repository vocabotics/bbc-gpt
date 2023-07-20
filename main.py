import asyncio
import openai
import json

# Load configuration from JSON file
with open('config.json') as json_file:
    config = json.load(json_file)

# Set configuration parameters
openai.api_key = config['api_key']
openai.api_base = config['api_base']
LISTEN_PORT = config['listen_port']
MODEL = config['model']

async def handle_connection(reader, writer):
    try:
        print("New connection established...")

        # loop to continuously read data until [[END]] delimiter is received
        data = b''
        while True:
            print("Waiting for data...")
            chunk = await reader.read(100)
            if not chunk:
                break
            data += chunk
            if b'[[END]]' in data:
                break

        message = data.decode().strip()
        print(f"Received message: {message}")

        # remove protocol delimiters
        if message.startswith("[[START]]") and message.endswith("[[END]]"):
            message = message[len("[[START]]"):-len("[[END]]")]

        # send message to OpenAI API
        print("Sending message to OpenAI API...")
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ]
        )

        # print user and assistant messages
        for message in response.choices[0].message['content']:
            if message['role'] == 'user':
                print(f"User: {message['content']}")
            elif message['role'] == 'assistant':
                print(f"Assistant: {message['content']}")

        # send response back to client
        print("Sending response back to client...")
        writer.write(f"[[START]]{response.choices[0].message['content']}[[END]]\n".encode())
        await writer.drain()

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # close connection
        print("Closing connection...")
        writer.close()

async def main():
    server = await asyncio.start_server(
        handle_connection, "localhost", LISTEN_PORT)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

try:
    asyncio.run(main())
except Exception as e:
    print(f"An error occurred in main: {e}")
