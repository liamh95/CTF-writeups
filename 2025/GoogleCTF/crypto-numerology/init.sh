# Example for your script that runs init_cryptanalysis.py
# (Ensure set_secrets.sh has run and created secrets.env)

# if [ ! -f "secrets.env" ]; then
#     echo "ERROR: secrets.env not found. Please run set_secrets.sh first."
#     exit 1
# fi
# source secrets.env # Load SECRET_TARGET_NONCE_HEX, SECRET_TARGET_COUNTER_INT, KNOWN_KEY_ACTIVE_MATERIAL_HEX, KNOWN_KEY_STRUCTURE

# if [ ! -f "flag.txt" ]; then
#     echo "ERROR: flag.txt not found."
#     exit 1
# fi
# FLAG_STRING=$(cat flag.txt)

# OUTPUT_PKG_FILE="./ctf_challenge_package.json" # This is what your linear_cryptanalysis.sh reads
ROUNDS=1
MESSAGE_SIZE=64
NUM_NONCE_VARS=32
NUM_COUNTER_VARS=32

# echo "Running init_cryptanalysis.py to generate challenge package..."

OUTPUT_PKG_FILE="./pls.json"
SECRET_TARGET_NONCE_HEX="000000800000000000000000"
SECRET_TARGET_COUNTER_INT=2147483648
KNOWN_KEY_ACTIVE_MATERIAL_HEX="5c54700231f4727bf7d49234e7bbb1c9"
FLAG_STRING="What the fuck did you just fucking say abo"

#python3 crypto_numerology.py \
python3 ./__pycache__/crypto_numerology.cpython-312.pyc \
    --output_file "${OUTPUT_PKG_FILE}" \
    --flag_string "${FLAG_STRING}" \
    --rounds ${ROUNDS} \
    --message_size_bytes ${MESSAGE_SIZE} \
    --known_key_active_material_hex "${KNOWN_KEY_ACTIVE_MATERIAL_HEX}" \
    --secret_target_nonce_hex "${SECRET_TARGET_NONCE_HEX}" \
    --secret_target_counter_int ${SECRET_TARGET_COUNTER_INT} \
    --num_nonce_variations ${NUM_NONCE_VARS} \
    --num_counter_variations ${NUM_COUNTER_VARS} \
