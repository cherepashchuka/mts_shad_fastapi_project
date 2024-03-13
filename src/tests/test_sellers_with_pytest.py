import pytest
from fastapi import status
from sqlalchemy import select

from src.models import books, sellers
from src.configurations.security import hashing_password


# POST /seller test
@pytest.mark.asyncio
async def test_create_seller(async_client):
    data = {
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "email": "ivanov@ivanov.ru",
        "password": "123abc123"
    }
    response = await async_client.post("/api/v1/seller/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()

    assert result_data == {
        "id": result_data["id"],
        "first_name": "Ivan",
        "last_name": "Ivanov",
        "email": "ivanov@ivanov.ru",
    }


# GET /seller test
@pytest.mark.asyncio
async def test_get_sellers(db_session, async_client):
    seller_1 = sellers.Seller(
        first_name="Petr",
        last_name="Petrov",
        email="petrov@petrov.ru",
        password=hashing_password("123ssss123")
    )
    seller_2 = sellers.Seller(
        first_name="Vasya",
        last_name="Vasyanov",
        email="vasyanov@vasyanov.ru",
        password=hashing_password("123lll123")
    )

    db_session.add_all([seller_1, seller_2])
    await db_session.flush()

    response = await async_client.get("/api/v1/seller/")

    assert response.status_code == status.HTTP_200_OK

    assert len(response.json()["sellers"]) == 2

    assert response.json() == {
        "sellers": [
            {
                "id": seller_1.id,
                "first_name": "Petr",
                "last_name": "Petrov",
                "email": "petrov@petrov.ru",
            },
            {
                "id": seller_2.id,
                "first_name": "Vasya",
                "last_name": "Vasyanov",
                "email": "vasyanov@vasyanov.ru",
            },
        ]
    }


# GET /seller/{seller_id}
@pytest.mark.asyncio
async def test_get_single_seller(db_session, async_client):
    seller_1 = sellers.Seller(
        first_name="Petr",
        last_name="Petrov",
        email="petrov@petrov.ru",
        password=hashing_password("123ssss123")
    )
    seller_2 = sellers.Seller(
        first_name="Vasya",
        last_name="Vasyanov",
        email="vasyanov@vasyanov.ru",
        password=hashing_password("123lll123")
    )
    seller_data_for_token = {
        "email": "petrov@petrov.ru",
        "password": "123ssss123"
    }

    db_session.add_all([seller_1, seller_2])
    await db_session.flush()

    response = await async_client.post("/api/v1/token/", json=seller_data_for_token)

    assert response.status_code == status.HTTP_201_CREATED

    seller_token = response.json()["access_token"]

    book = books.Book(
        author="Robert Martin",
        title="Wrong Code",
        year=2007,
        count_pages=104,
        seller_id=seller_1.id
    )

    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(
        f"/api/v1/seller/{seller_1.id}",
        headers={"Authorization": f"Bearer {seller_token}"}
    )

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "id": seller_1.id,
        "first_name": "Petr",
        "last_name": "Petrov",
        "email": "petrov@petrov.ru",
        "books": [
            {"id": book.id,
             "author": "Robert Martin",
             "title": "Wrong Code",
             "year": 2007,
             "count_pages": 104,
             "seller_id": seller_1.id
             }
        ]
    }


# DELETE /seller/{seller_id} test
@pytest.mark.asyncio
async def test_delete_seller(db_session, async_client):
    seller = sellers.Seller(
        first_name="Petr",
        last_name="Petrov",
        email="petrov@petrov.ru",
        password=hashing_password("123ssss123")
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.delete(f"/api/v1/seller/{seller.id}")

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    all_sellers = await db_session.execute(select(sellers.Seller))
    res = all_sellers.scalars().all()
    assert len(res) == 0

# PUT /seller/{seller_id} test
@pytest.mark.asyncio
async def test_update_seller(db_session, async_client):
    seller = sellers.Seller(
        first_name="Petr",
        last_name="Petrov",
        email="petrov@petrov.ru",
        password=hashing_password("123ssss123")
    )

    db_session.add(seller)
    await db_session.flush()

    response = await async_client.put(
        f"/api/v1/seller/{seller.id}",
        json={
            "id": seller.id,
            "first_name": "Petro",
            "last_name": "Petrolkin",
            "email": "petro@petro.ru",
        }
    )

    assert response.status_code == status.HTTP_200_OK
    await db_session.flush()

    res = await db_session.get(sellers.Seller, seller.id)
    assert res.id == seller.id
    assert res.first_name == "Petro"
    assert res.last_name == "Petrolkin"
    assert res.email == "petro@petro.ru"
