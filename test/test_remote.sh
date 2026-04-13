URL=34.22.135.113
curl -X POST "http://${URL}:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "BuildingType": "Spaceship",
    "PropertyType": "Office",
    "YearBuilt": "1990",
    "Surface": -25,
    "ExtraField": 1
  }'
