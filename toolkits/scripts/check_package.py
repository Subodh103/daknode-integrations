"""Build a wheel and verify an isolated core consumer without framework installs."""
import email
import json
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    temp = Path(tempfile.mkdtemp(prefix="daknode-python-toolkit-consumer-"))
    subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(temp), str(ROOT)], check=True)
    wheel = next(temp.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert any(name.endswith("/licenses/LICENSE") for name in names)
        assert all(not name.startswith(("tests/", "app/", ".agent/", ".env")) for name in names)
        metadata = email.message_from_bytes(archive.read(next(name for name in names if name.endswith("/METADATA"))))
        assert metadata["Name"] == "daknode-toolkit" and metadata["License-Expression"] == "MIT"
        urls = "\n".join(metadata.get_all("Project-URL"))
        assert "https://daknode.com/security/reporting/" in urls
        assert "https://github.com/Subodh103/daknode-integrations" in urls
    target = temp / "consumer"
    venv.EnvBuilder(with_pip=True).create(target)
    python = target / "bin" / "python"
    subprocess.run([str(python), "-m", "pip", "install", str(wheel)], check=True, stdout=subprocess.DEVNULL)
    code = '''
import importlib.util
import httpx
from daknode_toolkit import DakNodeToolkit
assert all(importlib.util.find_spec(name) is None for name in ("langchain_core", "crewai", "llama_index"))
calls=[]
def response(request):
    calls.append(request)
    return httpx.Response(200,json={"inbox_id":"11111111-1111-4111-8111-111111111111"})
with DakNodeToolkit(api_key="synthetic-consumer-only",inbox_id="11111111-1111-4111-8111-111111111111",_transport=httpx.MockTransport(response)) as toolkit:
    assert calls == []
    assert len(toolkit.functions()) == 6
    assert toolkit.check_connection()["scope"] == "inbox"
    assert len(calls) == 1
'''
    subprocess.run([str(python), "-c", code], check=True, cwd=temp)
    print(json.dumps({"wheel_metadata": "pass", "fresh_core_consumer": "pass", "frameworks_not_installed": True}))


if __name__ == "__main__":
    main()
