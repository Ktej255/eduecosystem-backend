from passlib.context import CryptContext

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Test local hashing and verification
new_hash = pwd.hash('Tej@1106')
print(f'New hash: {new_hash}')
print(f'Verify new hash: {pwd.verify("Tej@1106", new_hash)}')

# Test with the production hash
prod_hash = '$2b$12$aV6BbaHDjSzAE.Ik9.XOjusyr1/TR24ovvdok0LSuFNSJWRmtY.Ne'
print(f'\nProd hash length: {len(prod_hash)}')
try:
    result = pwd.verify('Tej@1106', prod_hash)
    print(f'Verify prod hash: {result}')
except Exception as e:
    print(f'Error verifying prod hash: {e}')
