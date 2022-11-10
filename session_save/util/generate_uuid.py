import hashlib
import uuid

def generate_UUID(uuid_type):
    generated_uuid = str(uuid.uuid4())
    if uuid_type:
        return generated_uuid
    else:
        return generated_uuid.replace("-", "")

def get_seed(*args):
    m = hashlib.md5()
    m.update(b"".join([arg.encode("utf-8") for arg in args]))
    return m.hexdigest()

def generate_device_id(seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode("utf-8") + volatile_seed.encode("utf-8"))
        return "android-" + m.hexdigest()[:16]

def generate_all_uuids(username, password):
    phone_id = generate_UUID(uuid_type=True)
    uuid = generate_UUID(uuid_type=True)
    client_session_id = generate_UUID(uuid_type=True)
    advertising_id = generate_UUID(uuid_type=True)
    device_id = generate_device_id(get_seed(username, password))
    uuids = {
            "uuids":
                {
                    "phone_id": phone_id,
                    "uuid":uuid,
                    "client_session_id" : client_session_id,
                    "advertising_id": advertising_id,
                    "device_id": device_id
                }
    }
    return uuids