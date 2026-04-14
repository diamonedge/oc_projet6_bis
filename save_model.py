from __future__ import annotations

from decimal import Decimal
import pandas as pd
import numpy as np

import json
from pathlib import Path

#Selection
from sklearn.model_selection import (
    train_test_split,
    GridSearchCV,
    cross_validate,
)
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error,root_mean_squared_error
from sklearn.inspection import permutation_importance

#Preprocess
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

#Modèles
from sklearn.ensemble import RandomForestRegressor
from sklearn.dummy import DummyRegressor

from sklearn.pipeline import Pipeline

#Bento ML
import bentoml

def write_validation_config(df, output_path: str = "validation_config.json") -> None:
    config = {
        "allowed_building_types": sorted(
            df["BuildingType"].dropna().astype(str).str.strip().unique().tolist()
        ),
        "allowed_property_types": sorted(
            df["PropertyType"].dropna().astype(str).str.strip().unique().tolist()
        ),
        "decade_min": 1800,
        "decade_max": 2100,
        "surface_min": 1.0,
        "surface_max": 10_000_000.0,
    }

    Path(output_path).write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

def flag_outliers_group_iqr(data, group_col, value_col, k=1.5, min_group_size=30):
    out = pd.Series(False, index=data.index)

    group_sizes = data[group_col].value_counts()
    valid_groups = group_sizes[group_sizes >= min_group_size].index

    for g in valid_groups:
        idx = data[group_col] == g
        s = data.loc[idx, value_col]

        q1 = s.quantile(0.25)
        q3 = s.quantile(0.75)
        iqr = q3 - q1

        low = q1 - k * iqr
        high = q3 + k * iqr

        out.loc[idx] = (s < low) | (s > high)

    return out

print("Reading CSV ...")
building_consumption = pd.read_csv("2016_Building_Energy_Benchmarking.csv")

print("Filtering ...")
building_consumption=building_consumption[building_consumption['SiteEUIWN(kBtu/sf)'].notnull()]
building_consumption=building_consumption[building_consumption['SiteEnergyUseWN(kBtu)'].notnull()]
building_consumption=building_consumption[building_consumption['NumberofBuildings']!=111]
building_consumption=building_consumption[building_consumption['Outlier'].isnull()]
building_consumption=building_consumption[building_consumption['ComplianceStatus']== 'Compliant']
building_consumption=building_consumption[building_consumption['PrimaryPropertyType'].isin(['Hotel', 'Other', 'Mixed Use Property', 'K-12 School',
       'University', 'Small- and Mid-Sized Office','Self-Storage Facility', 'Warehouse', 'Large Office',
       'Senior Care Community', 'Medical Office', 'Retail Store','Hospital', 'Distribution Center','Worship Facility', 'Supermarket / Grocery Store', 'Laboratory',
       'Refrigerated Warehouse', 'Restaurant', 'Office'])]

print("Adding columns ...")
building_consumption["BuildingAge"] = (2015-building_consumption["YearBuilt"])
building_consumption["Decade"] = (building_consumption["YearBuilt"] // 10) * 10

print("Cleaning columns ...")
building_consumption=building_consumption.drop([
'LargestPropertyUseType'
,'PropertyName'
,'Neighborhood'
,'LargestPropertyUseTypeGFA'
,'SecondLargestPropertyUseType'
,'SecondLargestPropertyUseTypeGFA'
,'ThirdLargestPropertyUseType'
,'ThirdLargestPropertyUseTypeGFA'
,'YearsENERGYSTARCertified'
,'ENERGYSTARScore'
,'Comments'
,'Outlier'
,'TaxParcelIdentificationNumber'
,'CouncilDistrictCode'
,'LargestPropertyUseType'
,'SecondLargestPropertyUseType'
,'ThirdLargestPropertyUseType'
,'LargestPropertyUseType'
,'Electricity(kWh)'
,'NaturalGas(therms)'
,'SiteEnergyUse(kBtu)'
,'SourceEUI(kBtu/sf)'
,'SiteEUI(kBtu/sf)'
,'Latitude'
,'Longitude'
,'GHGEmissionsIntensity'
,'Address'
,'ComplianceStatus'
,'DataYear'
,'SteamUse(kBtu)'
,'City'
,'State'
,'ZipCode'
,'DefaultData'
,'SourceEUIWN(kBtu/sf)'
,'NaturalGas(kBtu)'
,'NumberofBuildings'
,'TotalGHGEmissions'
,'PropertyGFAParking'
,'PropertyGFABuilding(s)'
,'ListOfAllPropertyUseTypes'
,'SiteEUIWN(kBtu/sf)'
,'OSEBuildingID'
,'Electricity(kBtu)'
,'YearBuilt'
], axis=1)

building_consumption=building_consumption.rename(columns={
    "SiteEnergyUseWN(kBtu)": "EnergyConsumption"
    ,"PropertyGFATotal":"Surface"
    , "PrimaryPropertyType":"PropertyType"
    , "NumberofFloors":"Floors"
    })

print("Adding features ...")

building_consumption["log_EnergyConsumption"] = np.log1p(building_consumption["EnergyConsumption"])
building_consumption["log_EUI"] = np.log1p(building_consumption["EnergyConsumption"] / building_consumption["Surface"])
building_consumption["log_Surface"] = np.log1p(building_consumption["Surface"])
building_consumption["outlier_surface"] = flag_outliers_group_iqr(building_consumption, "BuildingType", "log_Surface")
building_consumption["outlier_eui"] = flag_outliers_group_iqr(building_consumption, "BuildingType", "log_EUI")
building_consumption["SurfacePerFloor"] = building_consumption["Surface"]/(building_consumption["Floors"])

building_consumption.info()


print("Model parameters ...")
X=building_consumption[['Surface','PropertyType','Decade','BuildingType']]
y=building_consumption.EnergyConsumption

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

colonnes_numeriques = ['Surface']
colonnes_categorielles = ['PropertyType','Decade','BuildingType']

# Prétraitement pour RandomForest
preprocessor_rf = ColumnTransformer(
    transformers=[
        ("num", "passthrough", colonnes_numeriques),
        ("cat", OneHotEncoder(handle_unknown="ignore"), colonnes_categorielles),
    ]
)

model = Pipeline([
        ("preprocessing", preprocessor_rf),
        ("model", RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=-1))
    ])

print("Training model ...")
model.fit(X_train, y_train)

print("BentoML ...")

write_validation_config(building_consumption)

bento_model = bentoml.sklearn.save_model("seattle_energy_model",model,
    metadata={
        "target": "EnergyConsumption",
        "features": ["BuildingType", "PropertyType", "Decade", "Surface"],
    },
)

print(bento_model)
