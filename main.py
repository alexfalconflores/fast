from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy import Column,Integer,String,Float,create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import pyodbc

SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://192.168.3.102/gps_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de base de datos para dispositivos GPS
class GPSDeviceDB(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
# Crear las tablas en la base de datos (si no existen)
Base.metadata.create_all(bind=engine)

# Pydantic model para la API
class GPSDevice(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float

    class Config:
        orm_mode = True

app = FastAPI()


# Dependencia para obtener sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas para la API
@app.get("/devices", response_model=list[GPSDevice])
def get_devices(db: Session = Depends(get_db)):
    return db.query(GPSDeviceDB).all()

@app.post("/devices", response_model=GPSDevice)
def add_device(device: GPSDevice, db: Session = Depends(get_db)):
    db_device = GPSDeviceDB(id=device.id, name=device.name, latitude=device.latitude, longitude=device.longitude)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@app.get("/devices/{device_id}", response_model=GPSDevice)
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(GPSDeviceDB).filter(GPSDeviceDB.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@app.delete("/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(GPSDeviceDB).filter(GPSDeviceDB.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    db.delete(device)
    db.commit()
    return {"message": "Device deleted successfully"}