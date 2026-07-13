import pytest


@pytest.mark.asyncio
async def test_create_product(client):
    response = await client.post(
        "/product/create",
        json={"title": "Laptop", "desc": "Gaming laptop", "price": "1500.00"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Product created"
    assert data["data"]["title"] == "Laptop"
    assert data["data"]["price"] == "1500.00"


@pytest.mark.asyncio
async def test_create_product_invalid_title(client):
    response = await client.post(
        "/product/create",
        json={"title": "12345", "price": "100.00"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_negative_price(client):
    response = await client.post(
        "/product/create",
        json={"title": "Phone", "price": "-50.00"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_products(client):
    await client.post(
        "/product/create",
        json={"title": "Mouse", "price": "25.00"},
    )
    await client.post(
        "/product/create",
        json={"title": "Keyboard", "price": "75.00"},
    )

    response = await client.get("/product/list")

    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Products"
    assert data["count"] == 2
    assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_detail_product(client):
    create_response = await client.post(
        "/product/create",
        json={"title": "Monitor", "desc": "4K", "price": "400.00"},
    )
    product_id = create_response.json()["data"]["id"]

    response = await client.get(f"/product/detail/{product_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Monitor"
    assert data["desc"] == "4K"


@pytest.mark.asyncio
async def test_detail_product_not_found(client):
    response = await client.get("/product/detail/999")

    assert response.status_code == 404
    assert "topilmadi" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_product(client):
    create_response = await client.post(
        "/product/create",
        json={"title": "Tablet", "price": "300.00"},
    )
    product_id = create_response.json()["data"]["id"]

    response = await client.patch(
        f"/product/update/{product_id}",
        json={"title": "Tablet Pro", "price": "450.00"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["msg"] == "Product updated"
    assert data["data"]["title"] == "Tablet Pro"
    assert data["data"]["price"] == "450.00"


@pytest.mark.asyncio
async def test_update_product_not_found(client):
    response = await client.patch(
        "/product/update/999",
        json={"title": "Ghost"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product(client):
    create_response = await client.post(
        "/product/create",
        json={"title": "Headphones", "price": "120.00"},
    )
    product_id = create_response.json()["data"]["id"]

    response = await client.delete(f"/product/delete/{product_id}")

    assert response.status_code == 200
    assert response.json()["msg"] == "Product deleted"

    detail_response = await client.get(f"/product/detail/{product_id}")
    assert detail_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_not_found(client):
    response = await client.delete("/product/delete/999")

    assert response.status_code == 404
