import json
import base64
from cloudpathlib import S3Path

# Define the single source of truth for the S3 path
SECRETS_URI = "s3://alpha-contracts-etl/secrets/secrets.json"

def get_secrets_v2() -> dict:
    try:
        # 1. Single, Correct Read from S3 (Resolves the decoding error)
        secrets_path = S3Path(SECRETS_URI)
        # Use 'r' mode with 'utf-8' encoding for correct text parsing
        with secrets_path.open("r", encoding="utf-8") as f:
            secrets = json.load(f) # 'secrets' is now a Python dictionary in memory

        # 2. Process Secrets in Memory Based on Format/Key
        processed_secrets = {}
        print("--- Processing Secrets ---")

        for key, value in secrets.items():
            if key in ["jag_private_key", "another_base64_key"]:
                # --- Format A: Base64 Decoding ---
                decoded_value = base64.b64decode(value.encode("utf-8")).decode("utf-8")
                processed_secrets[key] = decoded_value
                print(f"Key: {key} (Base64) processed.")

            elif key in ["jag_host_key", "ssh_public_key"]:
                # --- Format B: SSH Key (already plain text) ---
                processed_secrets[key] = value
                print(f"Key: {key} (SSH) saved directly.")

            elif key.startswith("db_"):
                # --- Format C: Plain Text Credentials (no processing needed) ---
                processed_secrets[key] = value
                print(f"Key: {key} (Plain Text) saved directly.")

            else:
                # Catch-all for unknown secrets
                processed_secrets[key] = value
                print(f"Key: {key} (Unknown) saved directly.")


        print("--------------------------")

        # --- CORRECTION 1: Print the dictionary you created and will return (processed_secrets) ---
        #print("--- FINAL PROCESSED SECRETS ---")
        #for key, value in processed_secrets.items():
        #   print(f"Key: {key}, Value: {value}")
        #print("-------------------------------")

        # access the key from the processed dictionary ---


        print("jag_host_key=",processed_secrets["jag_host_key"])
        print("jag_private_key=",processed_secrets["jag_private_key"])
        print("client_id=",processed_secrets["client_id"])
        print("client_secret=",processed_secrets["client_secret"])

        return processed_secrets

    except Exception as e:
        print(f"ERROR: Failed to load secrets. Reason: {e}")
        raise

# ----------------------------------------------------------------------
# 🚀 SINGLE, CORRECT EXECUTION BLOCK
# ----------------------------------------------------------------------

if __name__ == "__main__":
    try:
        # This calls the function and initiates the whole process, including printing
        final_secrets = get_secrets_v2()

        # Example of using the retrieved secrets outside the function
        # print(f"\nApp retrieved {len(final_secrets)} total secrets.")

    except Exception:
        # If the function raises an exception, the program stops gracefully here
        print("\nFATAL ERROR: Application startup aborted due to secrets failure.")