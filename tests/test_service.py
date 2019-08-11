import json


async def test_should_make_mucho_grande_requests_to_service(client):
    # for i in $(seq 1000 $END); do curl --header "Content-Type: application/json" --request POST --data '{"eventId": "e1", "userId": "b26e6dc4-1672-4068-ad2f-54be1c39e18c"}' http://localhost:8080/register/event; done
    e1 = json.dumps({"eventId": "e1", "userId": "b26e6dc4-1672-4068-ad2f-54be1c39e18c"})

    async def a_range(n):
        for _ in range(n):
            yield _

    responses = list()
    async for _ in a_range(1000):
        responses.append(await client.post('/register/event', data=e1))

    assert all(r.status == 200 for r in responses)
