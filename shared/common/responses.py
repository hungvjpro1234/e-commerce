from rest_framework.response import Response


def ok(data=None, message="Success", status_code=200):
    return Response({"message": message, "data": data}, status=status_code)


def fail(message, errors=None, status_code=400):
    payload = {"message": message}
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)
