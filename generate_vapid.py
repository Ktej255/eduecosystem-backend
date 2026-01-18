import secrets
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def generate_vapid_keys():
    # Generate P-256 private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    
    # Get private bytes (raw)
    private_key_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
    
    # Get public bytes (raw, uncompressed)
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    public_key_bytes = b'\x04' + \
                       public_numbers.x.to_bytes(32, 'big') + \
                       public_numbers.y.to_bytes(32, 'big')
    
    # URL-safe base64 encoding without padding
    private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
    
    return private_key_b64, public_key_b64

if __name__ == "__main__":
    priv, pub = generate_vapid_keys()
    with open("keys.txt", "w") as f:
        f.write(f"PRIVATE_KEY={priv}\n")
        f.write(f"PUBLIC_KEY={pub}\n")
    print("Keys written to keys.txt")

