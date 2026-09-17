def test_pdf_upload(client, auth_headers):
    with open("tests/mock_invoice.pdf", "rb") as f:
        resp = client.post("/api/v1/documents/upload", files=[("files", ("mock_invoice.pdf", f, "application/pdf"))], headers=auth_headers)
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["file_type"] == "application/pdf"

def test_image_upload(client, auth_headers):
    with open("tests/mock_invoice.jpg", "rb") as f:
        resp = client.post("/api/v1/documents/upload", files=[("files", ("mock_invoice.jpg", f, "image/jpeg"))], headers=auth_headers)
    assert resp.status_code == 200

def test_png_upload(client, auth_headers):
    with open("tests/mock_invoice.png", "rb") as f:
        resp = client.post("/api/v1/documents/upload", files=[("files", ("mock_invoice.png", f, "image/png"))], headers=auth_headers)
    assert resp.status_code == 200

def test_multiple_file_upload(client, auth_headers):
    with open("tests/mock_invoice.pdf", "rb") as f1, open("tests/mock_invoice.jpg", "rb") as f2:
        resp = client.post(
            "/api/v1/documents/upload", 
            files=[
                ("files", ("mock1.pdf", f1, "application/pdf")),
                ("files", ("mock2.jpg", f2, "image/jpeg"))
            ], 
            headers=auth_headers
        )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_document_get_file(client, auth_headers):
    with open("tests/mock_invoice.pdf", "rb") as f:
        upload_resp = client.post("/api/v1/documents/upload", files=[("files", ("mock_invoice.pdf", f, "application/pdf"))], headers=auth_headers)
    
    doc_id = upload_resp.json()[0]["id"]
    
    file_resp = client.get(f"/api/v1/documents/{doc_id}/file", headers=auth_headers)
    assert file_resp.status_code == 200
    assert file_resp.headers["content-type"] == "application/pdf"
