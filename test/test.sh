URL=localhost
echo "################################# Test qui doit renvoyer KO"
curl -X POST "http://${URL}:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "BuildingType": "Spaceship",
    "PropertyType": "Office",
    "YearBuilt": "1990",
    "Surface": -25,
    "ExtraField": 1
  }'
echo ""
echo "################################## Test qui doit renvoyer OK"
curl -X POST "http://${URL}:3000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "BuildingType": "NonResidential",
    "PropertyType": "Large Office",
    "YearBuilt": 1990,
    "Surface": 103566.0
  }'
echo ""
echo "################################# On attends une consommation d'environ 8 500 000 de Kbtu"
