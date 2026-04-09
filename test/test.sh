curl -X POST "http://127.0.0.1:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "BuildingType": "Spaceship",
    "PropertyType": "Office",
    "YearBuilt": "1990",
    "Surface": -25,
    "ExtraField": 1
  }'
