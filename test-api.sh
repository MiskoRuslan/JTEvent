#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== REGISTER USER ==="
curl -X POST $BASE_URL/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
  }'

echo -e "\n\n=== LOGIN ==="
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access')
echo "Token: $TOKEN"

echo -e "\n\n=== CREATE EVENT ==="
curl -X POST $BASE_URL/api/events/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Tech Meetup 2024",
    "description": "Monthly tech meetup for developers",
    "date": "2024-12-31T18:00:00Z",
    "location": "Tech Hub, Main Street",
    "category": "tech",
    "max_attendees": 50,
    "tags": "tech, networking, developers",
    "is_published": true
  }'

echo -e "\n\n=== LIST EVENTS ==="
curl -X GET "$BASE_URL/api/events/"

echo -e "\n\n=== SEARCH EVENTS ==="
curl -X GET "$BASE_URL/api/events/?search=tech"

echo -e "\n\n=== FILTER BY CATEGORY ==="
curl -X GET "$BASE_URL/api/events/?category=tech"

echo -e "\n\n=== REGISTER FOR EVENT ==="
curl -X POST $BASE_URL/api/events/1/register/ \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== MY REGISTRATIONS ==="
curl -X GET $BASE_URL/api/registrations/my_registrations/ \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== MY EVENTS ==="
curl -X GET $BASE_URL/api/events/my_events/ \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== GET EVENT ATTENDEES ==="
curl -X GET $BASE_URL/api/events/1/attendees/ \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== UNREGISTER FROM EVENT ==="
curl -X DELETE $BASE_URL/api/events/1/unregister/ \
  -H "Authorization: Bearer $TOKEN"

echo -e "\n\n=== UPDATE EVENT ==="
curl -X PATCH $BASE_URL/api/events/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Tech Meetup 2024"
  }'

echo -e "\n\n✅ Testing complete!"
