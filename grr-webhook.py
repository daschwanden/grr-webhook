# Copyright 2025 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START grr-webhook]
#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from openrelik_api_client.api_client import APIClient
from openrelik_api_client.workflows import WorkflowsAPI
from typing import Any

import json
import logging
import os

class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers))
        self._set_response()
        self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        """Handles POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data_bytes = self.rfile.read(content_length)

        # For robust JSON handling, you might check the Content-Type header
        content_type = self.headers.get('Content-Type', '')
        is_json_request = 'application/json' in content_type.lower()

        if not is_json_request:
            logging.info("Warning: Received POST request without 'application/json' Content-Type.")
            # You might choose to reject non-JSON requests here if strictly required
            # For this example, we'll still try to process it as JSON in process_post_data

        parsed_data, status_message = self.process_post_data(post_data_bytes)

        if parsed_data is not None:
            self.send_response(200)
            response_content_type = 'application/json' # Respond with JSON if successfully parsed
            response_payload = json.dumps({
                "status": "success",
                "received_data": parsed_data,
                "message": status_message
            })
            logging.info(response_payload)
            #self.process_payload(response_payload)
        else:
            # Handle cases where parsing failed
            if "Invalid JSON" in status_message:
                self.send_response(400) # Bad Request
            elif "decode" in status_message.lower(): # Unicode decode error
                self.send_response(400) # Bad Request
            else:
                self.send_response(500) # Internal Server Error
            response_content_type = 'application/json' # Still good to respond with JSON for errors
            response_payload = json.dumps({
                "status": "error",
                "message": status_message
            })

        self.send_header('Content-type', response_content_type)
        self.end_headers()
        self.wfile.write(response_payload.encode('utf-8'))


    def process_payload(self, payload_string):
        """
        Processes the payload data
        1) Stream from GRR to OpenRelik
        2) Kick off OpenRelik Workflow
        """
        payload = json.loads(payload_string)
        received_data = payload.get("received_data")
        if received_data:
           logging.info(f"received_data: {received_data}")

    def process_post_data(self, data_bytes):
        """
        Processes the raw bytes of the POST data, assuming it's JSON.
        Returns a tuple: (parsed_json_object, status_message)
        parsed_json_object will be None if parsing fails.
        """
        try:
            # 1. Decode the bytes to a string (UTF-8 is common for JSON)
            data_string = data_bytes.decode('utf-8')
            #print(f"Received raw string data: {data_string}")
        except UnicodeDecodeError:
            error_msg = "Error: Could not decode POST data from bytes (expected UTF-8)."
            logging.error(error_msg)
            return None, error_msg

        try:
            # 2. Parse the string into a Python dictionary (or list if it's a JSON array)
            parsed_json = json.loads(data_string)
            #print(f"Successfully parsed JSON: {parsed_json}")
            
            # You can now work with parsed_json as a Python dict/list
            # Example: Accessing a value if it's a dictionary
            # if isinstance(parsed_json, dict) and 'name' in parsed_json:
            #     print(f"Name from JSON: {parsed_json['name']}")

            return parsed_json, "JSON data processed successfully."
        except json.JSONDecodeError as e:
            error_msg = f"Error: Invalid JSON format in POST data. Details: {e}"
            logging.error(error_msg)
            return None, error_msg
        except Exception as e:
            # Catch any other unexpected errors during processing
            error_msg = f"An unexpected error occurred during JSON processing: {e}"
            logging.error(error_msg)
            return None, error_msg

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    http_server = server_class(server_address, handler_class)
    logging.info('Starting grr-webhook HTTP Server at port %d...\n', port)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    http_server.server_close()
    logging.info('Stopping grr-webhook HTTP Server...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
# [END grr-webhook]
