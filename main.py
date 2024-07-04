import os
import random
import string
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from databases import Database
import aiosqlite

app = FastAPI()

# Database URL from environment or use SQLite file for demonstration
DATABASE_URL = os.getenv('DATABASE_URL', "sqlite:///./test.db")

# Initialize databases instance
database = Database(DATABASE_URL)

# Pydantic model for registration request
class RegisterRequest(BaseModel):
    mobile_number: str

# Generate OTP (4 digits for simplicity)
def generate_otp():
    return ''.join(random.choices(string.digits, k=4))

# Route to register and generate OTP
@app.post("/register/")
async def register(reg_request: RegisterRequest):
    mobile_number = reg_request.mobile_number

    # Generate OTP
    otp = generate_otp()

    # Use aiosqlite for async SQLite operations
    async with aiosqlite.connect("./test.db") as db:
        # Check if mobile number already exists in the database
        async with db.execute("SELECT otp FROM users WHERE mobile_number=?", (mobile_number,)) as cursor:
            existing_record = await cursor.fetchone()

        if existing_record:
            # If mobile number exists, update the OTP and resend
            await db.execute("UPDATE users SET otp=? WHERE mobile_number=?", (otp, mobile_number))
            await db.commit()
        else:
            # If mobile number doesn't exist, insert new record
            await db.execute("INSERT INTO users (mobile_number, otp) VALUES (?, ?)", (mobile_number, otp))
            await db.commit()

    return {"message": f"OTP {otp} generated and registered for {mobile_number}"}

# Pydantic model for OTP verification request
class OTPVerifyRequest(BaseModel):
    mobile_number: str
    otp: str

# Route to verify OTP
@app.post("/verify-otp/")
async def verify_otp(otp_verify_request: OTPVerifyRequest):
    mobile_number = otp_verify_request.mobile_number
    otp = otp_verify_request.otp

    # Use aiosqlite for async SQLite operations
    async with aiosqlite.connect("./test.db") as db:
        async with db.execute("SELECT otp FROM users WHERE mobile_number=?", (mobile_number,)) as cursor:
            fetched_otp = await cursor.fetchone()

        if fetched_otp and fetched_otp[0] == otp:
            return {"message": "OTP verified successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid OTP")

# Entry point for the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
