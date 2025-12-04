import modal

# ---------------------
# NOT CONNECTED YET
# ---------------------

# Create a stub (name of your app)
stub = modal.Stub("API_Demo")

# Define the function that will run on Modal
@stub.function()
def run_app():
    # Put your dashboard or OCR code here
    # Example: just a simple print for testing
    print("Hello, Modal is running!")

# Deployable entry point
if __name__ == "__main__":
    with stub.run():
        run_app()

