from app import app, socketio
from app.models import HiddenRecentItem, History


def test_get_shopping_lists(user_client_with_household, household_id):
    response = user_client_with_household.get(
        f"/api/household/{household_id}/shoppinglist",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert "household_id" in data[0]
    assert data[0]["household_id"] == household_id
    assert "id" in data[0]
    assert "name" in data[0]


def test_add_item_by_name(user_client_with_household, shoppinglist_id, item_name):
    data = {"name": item_name}
    response = user_client_with_household.post(
        f"/api/shoppinglist/{shoppinglist_id}/add-item-by-name", json=data
    )
    assert response.status_code == 200


def test_get_items(user_client_with_household, shoppinglist_id_with_item, item_name):
    response = user_client_with_household.get(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/items"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert "name" in data[0]
    assert data[0]["name"] == item_name


def test_remove_item(user_client_with_household, shoppinglist_id_with_item, item_id):
    data = {"item_id": item_id}
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/item", json=data
    )
    assert response.status_code == 200
    response = user_client_with_household.get(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/items"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0


def get_recent_item_names(client, shoppinglist_id):
    response = client.get(f"/api/shoppinglist/{shoppinglist_id}/recent-items")
    assert response.status_code == 200
    return [e["name"] for e in response.get_json()]


def test_remove_item_appears_in_recent_items(
    user_client_with_household, shoppinglist_id_with_item, item_id, item_name
):
    data = {"item_id": item_id}
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/item", json=data
    )
    assert response.status_code == 200
    assert item_name in get_recent_item_names(
        user_client_with_household, shoppinglist_id_with_item
    )


def test_hard_remove_item(
    user_client_with_household, shoppinglist_id_with_item, item_id, item_name
):
    data = {"item_id": item_id, "hard": True}
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/item", json=data
    )
    assert response.status_code == 200
    response = user_client_with_household.get(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/items"
    )
    assert response.status_code == 200
    assert len(response.get_json()) == 0
    # hard removals are not recorded in the history
    assert item_name not in get_recent_item_names(
        user_client_with_household, shoppinglist_id_with_item
    )


def test_hard_remove_item_keeps_existing_recent_items(
    user_client_with_household, shoppinglist_id_with_item, item_id, item_name
):
    # remove the item normally, so it ends up in the recent items
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/item",
        json={"item_id": item_id},
    )
    assert response.status_code == 200
    # add it again and remove it hard
    response = user_client_with_household.post(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/add-item-by-name",
        json={"name": item_name},
    )
    assert response.status_code == 200
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/item",
        json={"item_id": item_id, "hard": True},
    )
    assert response.status_code == 200
    # the previously recorded recent item stays untouched
    assert item_name in get_recent_item_names(
        user_client_with_household, shoppinglist_id_with_item
    )


def test_hard_remove_items(
    user_client_with_household, shoppinglist_id_with_item, item_id, item_name
):
    # add a second item
    response = user_client_with_household.post(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/add-item-by-name",
        json={"name": "Second Item"},
    )
    assert response.status_code == 200
    response = user_client_with_household.get(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/items"
    )
    assert response.status_code == 200
    items = response.get_json()
    assert len(items) == 2

    data = {
        "items": [
            {"item_id": item_id, "hard": True},
            {
                "item_id": items[0]["id"]
                if items[0]["id"] != item_id
                else items[1]["id"]
            },
        ]
    }
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/items", json=data
    )
    assert response.status_code == 200
    response = user_client_with_household.get(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/items"
    )
    assert response.status_code == 200
    assert len(response.get_json()) == 0
    recent_names = get_recent_item_names(
        user_client_with_household, shoppinglist_id_with_item
    )
    # the hard removed item is not recorded, the soft removed one is
    assert item_name not in recent_names
    assert "Second Item" in recent_names


def test_hide_recent_item_preserves_history_and_response_shape(
    user_client_with_household,
    household_id,
    shoppinglist_id_with_item,
    item_id,
    item_name,
):
    client = user_client_with_household
    list_id = shoppinglist_id_with_item
    response = client.delete(
        f"/api/shoppinglist/{list_id}/item", json={"item_id": item_id}
    )
    assert response.status_code == 200
    history_count = History.query.filter_by(
        shoppinglist_id=list_id, item_id=item_id
    ).count()

    response = client.delete(
        f"/api/shoppinglist/{list_id}/recent-items/{item_id}"
    )
    assert response.status_code == 200
    assert client.delete(
        f"/api/shoppinglist/{list_id}/recent-items/{item_id}"
    ).status_code == 200

    assert item_name not in get_recent_item_names(client, list_id)
    assert History.query.filter_by(
        shoppinglist_id=list_id, item_id=item_id
    ).count() == history_count

    response = client.get(
        f"/api/household/{household_id}/shoppinglist?recent_limit=120"
    )
    assert response.status_code == 200
    shoppinglist = next(e for e in response.get_json() if e["id"] == list_id)
    assert item_name not in [e["name"] for e in shoppinglist["recentItems"]]
    assert "items" in shoppinglist


def test_hidden_recent_item_is_scoped_to_its_shopping_list(
    user_client_with_household,
    household_id,
    shoppinglist_id_with_item,
    item_id,
    item_name,
):
    client = user_client_with_household
    first_list_id = shoppinglist_id_with_item
    assert client.delete(
        f"/api/shoppinglist/{first_list_id}/item", json={"item_id": item_id}
    ).status_code == 200

    response = client.post(
        f"/api/household/{household_id}/shoppinglist", json={"name": "Second"}
    )
    assert response.status_code == 200
    second_list_id = response.get_json()["id"]
    second_item_name = "Second List Item"
    assert client.post(
        f"/api/shoppinglist/{second_list_id}/add-item-by-name",
        json={"name": second_item_name},
    ).status_code == 200
    second_item = next(
        item
        for item in client.get(
            f"/api/shoppinglist/{second_list_id}/items"
        ).get_json()
        if item["name"] == second_item_name
    )
    assert client.delete(
        f"/api/shoppinglist/{second_list_id}/item",
        json={"item_id": second_item["id"]},
    ).status_code == 200

    assert client.delete(
        f"/api/shoppinglist/{first_list_id}/recent-items/{item_id}"
    ).status_code == 200
    assert item_name not in get_recent_item_names(client, first_list_id)
    assert second_item_name in get_recent_item_names(client, second_list_id)
    assert HiddenRecentItem.find_by_ids(first_list_id, item_id)
    assert HiddenRecentItem.find_by_ids(second_list_id, item_id) is None


def test_hidden_recent_item_returns_after_a_new_checkoff(
    user_client_with_household,
    shoppinglist_id_with_item,
    item_id,
    item_name,
):
    client = user_client_with_household
    list_id = shoppinglist_id_with_item
    assert client.delete(
        f"/api/shoppinglist/{list_id}/item", json={"item_id": item_id}
    ).status_code == 200
    assert client.delete(
        f"/api/shoppinglist/{list_id}/recent-items/{item_id}"
    ).status_code == 200

    assert client.post(
        f"/api/shoppinglist/{list_id}/add-item-by-name", json={"name": item_name}
    ).status_code == 200
    assert client.delete(
        f"/api/shoppinglist/{list_id}/item",
        json={"item_id": item_id, "hard": True},
    ).status_code == 200
    assert item_name not in get_recent_item_names(client, list_id)

    assert client.post(
        f"/api/shoppinglist/{list_id}/add-item-by-name", json={"name": item_name}
    ).status_code == 200
    assert client.delete(
        f"/api/shoppinglist/{list_id}/item", json={"item_id": item_id}
    ).status_code == 200
    assert item_name in get_recent_item_names(client, list_id)


def test_hiding_recent_item_does_not_backfill_beyond_requested_limit(
    user_client_with_household,
    shoppinglist_id_with_item,
    item_id,
    item_name,
):
    client = user_client_with_household
    list_id = shoppinglist_id_with_item
    assert client.delete(
        f"/api/shoppinglist/{list_id}/item", json={"item_id": item_id}
    ).status_code == 200
    assert client.post(
        f"/api/shoppinglist/{list_id}/add-item-by-name",
        json={"name": "Second Recent Item"},
    ).status_code == 200
    second_item = next(
        e
        for e in client.get(f"/api/shoppinglist/{list_id}/items").get_json()
        if e["name"] == "Second Recent Item"
    )
    assert client.delete(
        f"/api/shoppinglist/{list_id}/item",
        json={"item_id": second_item["id"]},
    ).status_code == 200

    response = client.get(
        f"/api/shoppinglist/{list_id}/recent-items?limit=1"
    )
    assert response.status_code == 200
    first_recent_id = response.get_json()[0]["id"]
    assert client.delete(
        f"/api/shoppinglist/{list_id}/recent-items/{first_recent_id}"
    ).status_code == 200
    response = client.get(
        f"/api/shoppinglist/{list_id}/recent-items?limit=1"
    )
    assert response.status_code == 200
    assert response.get_json() == []


def test_cannot_hide_an_active_item(
    user_client_with_household,
    shoppinglist_id_with_item,
    item_id,
):
    response = user_client_with_household.delete(
        f"/api/shoppinglist/{shoppinglist_id_with_item}/recent-items/{item_id}"
    )
    assert response.status_code == 400
    assert len(
        user_client_with_household.get(
            f"/api/shoppinglist/{shoppinglist_id_with_item}/items"
        ).get_json()
    ) == 1


def test_hiding_recent_item_requires_authorization(client):
    response = client.delete(
        "/api/shoppinglist/1/recent-items/1"
    )
    assert response.status_code == 401


def test_hide_recent_item_emits_update_to_connected_clients(
    user_client_with_household,
    shoppinglist_id_with_item,
    item_id,
):
    client = user_client_with_household
    list_id = shoppinglist_id_with_item
    assert client.delete(
        f"/api/shoppinglist/{list_id}/item", json={"item_id": item_id}
    ).status_code == 200

    first = socketio.test_client(app, flask_test_client=client)
    second = socketio.test_client(app, flask_test_client=client)
    try:
        assert first.is_connected()
        assert second.is_connected()
        first.get_received()
        second.get_received()

        response = client.delete(
            f"/api/shoppinglist/{list_id}/recent-items/{item_id}"
        )
        assert response.status_code == 200
        for socket_client in (first, second):
            events = socket_client.get_received()
            assert any(
                event["name"] == "shoppinglist_item:recent_hide"
                and event["args"][0]["item_id"] == item_id
                for event in events
            )
    finally:
        first.disconnect()
        second.disconnect()
