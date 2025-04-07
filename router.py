from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, conint, constr
import database

app = FastAPI()


class Student(BaseModel):
    StudentID: conint(ge=0, le=999)
    Name: constr(min_length=1, max_length=100)
    Age: conint(ge=18)
    Address: constr(min_length=1, max_length=255)
    ContactNumber: constr(min_length=10, max_length=15)

#  Contact Model (For Update/Delete)
class ContactUpdate(BaseModel):
    ContactNumber: constr(min_length=10, max_length=15)


@app.get("/api/students")
async def get_students():
    query = """
        SELECT s.StudentID, s.Name, s.Age, s.Address, c.ContactNumber
        FROM Student s LEFT JOIN ContactNumber c ON s.StudentID = c.StudentID
    """
    return fetch_data(query, ["StudentID", "Name", "Age", "Address", "ContactNumber"])

# Fetch Single Student (GET)
@app.get("/api/students/{student_id}")
async def get_student(student_id: int):
    query = """
        SELECT s.StudentID, s.Name, s.Age, s.Address, c.ContactNumber
        FROM Student s LEFT JOIN ContactNumber c ON s.StudentID = c.StudentID
        WHERE s.StudentID=%s
    """
    return fetch_single_data(query, [student_id], ["StudentID", "Name", "Age", "Address", "ContactNumber"])

#  Insert Student & Contact Number (POST)
@app.post("/api/students")
async def add_student(student: Student):
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO Student (StudentID, Name, Age, Address) VALUES (%s, %s, %s, %s)",
                       (student.StudentID, student.Name, student.Age, student.Address))
        cursor.execute("INSERT INTO ContactNumber (StudentID, ContactNumber) VALUES (%s, %s)",
                       (student.StudentID, student.ContactNumber))
        connection.commit()
        return {"message": "Student registered successfully", "StudentID": student.StudentID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#  Update Student (PUT)
@app.put("/api/students/{student_id}")
async def update_student(student_id: int, student: Student):
    return update_data("UPDATE Student SET Name=%s, Age=%s, Address=%s WHERE StudentID=%s",
                       (student.Name, student.Age, student.Address, student_id))

#  Update Contact Number (PUT)
@app.put("/api/contact/{student_id}")
async def update_contact(student_id: int, contact: ContactUpdate):
    return update_data("UPDATE ContactNumber SET ContactNumber=%s WHERE StudentID=%s",
                       (contact.ContactNumber, student_id))

#  Delete Student & Contact (DELETE)
@app.delete("/api/students/{student_id}")
async def delete_student(student_id: int):
    return delete_data("DELETE FROM Student WHERE StudentID=%s", [student_id])

#  Delete Contact Only (DELETE)
@app.delete("/api/contact/{student_id}")
async def delete_contact(student_id: int):
    return delete_data("DELETE FROM ContactNumber WHERE StudentID=%s", [student_id])

# -------------------------------------------
#  Helper Functions (Database Operations)
# -------------------------------------------
def fetch_data(query, columns):
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def fetch_single_data(query, values, columns):
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        result = cursor.fetchone()
        if result:
            return dict(zip(columns, result))
        else:
            raise HTTPException(status_code=404, detail="Data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

def update_data(query, values):
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"message": "Data updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()

def delete_data(query, values):
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"message": "Data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        connection.close()


#  Status Model
class ApplicationStatus(BaseModel):
    StatusID: int
    StatusDescription: str



@app.get("/api/status/all")
async def get_all_status():
    query = "SELECT * FROM ApplicationStatus"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        statuses = cursor.fetchall()

        result = [
            {"StatusID": status[0], "StatusDescription": status[1]} for status in statuses
        ]
        return {"statuses": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.post("/api/status/add")
async def add_status(status: ApplicationStatus):
    query = "INSERT INTO ApplicationStatus (StatusID, StatusDescription) VALUES (%s, %s)"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (status.StatusID, status.StatusDescription))
        connection.commit()
        return {"message": "Status added successfully", "StatusID": status.StatusID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/status/update/{status_id}")
async def update_status(status_id: int, status: ApplicationStatus):
    query = "UPDATE ApplicationStatus SET StatusDescription = %s WHERE StatusID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (status.StatusDescription, status_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Status with ID {status_id} not found")

        return {"message": f"Status with ID {status_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.delete("/api/status/delete/{status_id}")
async def delete_status(status_id: int):
    query = "DELETE FROM ApplicationStatus WHERE StatusID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (status_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Status with ID {status_id} not found")

        return {"message": f"Status with ID {status_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


class Application(BaseModel):
    ApplicationID: int
    StudentID: int
    UnitID: str
    StatusID: int


@app.get("/api/application/all")
async def get_all_applications():
    query = "SELECT * FROM Application"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        applications = cursor.fetchall()

        result = [
            {
                "ApplicationID": app[0],
                "StudentID": app[1],
                "UnitID": app[2],
                "StatusID": app[3]
            }
            for app in applications
        ]
        return {"applications": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.post("/api/application/add")
async def add_application(application: Application):
    query = """
        INSERT INTO Application (ApplicationID, StudentID, UnitID, StatusID)
        VALUES (%s, %s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query,
                       (application.ApplicationID, application.StudentID, application.UnitID, application.StatusID))
        connection.commit()
        return {"message": "Application added successfully", "ApplicationID": application.ApplicationID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/application/update/{application_id}")
async def update_application(application_id: int, application: Application):
    query = """
        UPDATE Application 
        SET StudentID = %s, UnitID = %s, StatusID = %s 
        WHERE ApplicationID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (application.StudentID, application.UnitID, application.StatusID, application_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Application with ID {application_id} not found")

        return {"message": f"Application with ID {application_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.delete("/api/application/delete/{application_id}")
async def delete_application(application_id: int):
    query = "DELETE FROM Application WHERE ApplicationID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (application_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Application with ID {application_id} not found")

        return {"message": f"Application with ID {application_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


class Application(BaseModel):
    ApplicationID: int
    StudentID: int
    UnitID: str
    StatusID: int


@app.get("/api/application/all")
async def get_all_applications():
    query = "SELECT * FROM Application"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        applications = cursor.fetchall()

        result = [
            {
                "ApplicationID": app[0],
                "StudentID": app[1],
                "UnitID": app[2],
                "StatusID": app[3]
            }
            for app in applications
        ]
        return {"applications": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.post("/api/application/add")
async def add_application(application: Application):
    query = """
        INSERT INTO Application (ApplicationID, StudentID, UnitID, StatusID)
        VALUES (%s, %s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query,
                       (application.ApplicationID, application.StudentID, application.UnitID, application.StatusID))
        connection.commit()
        return {"message": "Application added successfully", "ApplicationID": application.ApplicationID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/application/update/{application_id}")
async def update_application(application_id: int, application: Application):
    query = """
        UPDATE Application 
        SET StudentID = %s, UnitID = %s, StatusID = %s 
        WHERE ApplicationID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (application.StudentID, application.UnitID, application.StatusID, application_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Application with ID {application_id} not found")

        return {"message": f"Application with ID {application_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.delete("/api/application/delete/{application_id}")
async def delete_application(application_id: int):
    query = "DELETE FROM Application WHERE ApplicationID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (application_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Application with ID {application_id} not found")

        return {"message": f"Application with ID {application_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


class Payment(BaseModel):
    PaymentID: int
    ApplicationID: int
    Amount: float
    PaymentDate: str



@app.get("/api/payment/all")
async def get_all_payments():
    query = "SELECT * FROM Payment"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        payments = cursor.fetchall()

        result = [
            {
                "PaymentID": payment[0],
                "ApplicationID": payment[1],
                "Amount": float(payment[2]),
                "PaymentDate": str(payment[3])
            }
            for payment in payments
        ]
        return {"payments": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.post("/api/payment/add")
async def add_payment(payment: Payment):
    query = """
        INSERT INTO Payment (PaymentID, ApplicationID, Amount, PaymentDate)
        VALUES (%s, %s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (payment.PaymentID, payment.ApplicationID, payment.Amount, payment.PaymentDate))
        connection.commit()
        return {"message": "Payment added successfully", "PaymentID": payment.PaymentID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.put("/api/payment/update/{payment_id}")
async def update_payment(payment_id: int, payment: Payment):
    query = """
        UPDATE Payment 
        SET ApplicationID = %s, Amount = %s, PaymentDate = %s
        WHERE PaymentID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (payment.ApplicationID, payment.Amount, payment.PaymentDate, payment_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Payment with ID {payment_id} not found")

        return {"message": f"Payment with ID {payment_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.delete("/api/payment/delete/{payment_id}")
async def delete_payment(payment_id: int):
    query = "DELETE FROM Payment WHERE PaymentID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (payment_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Payment with ID {payment_id} not found")

        return {"message": f"Payment with ID {payment_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


class Exam(BaseModel):
    ExamID: int
    UnitID: str
    ExamName: str
    MaxMarks: int



@app.get("/api/exam/all")
async def get_all_exams():
    query = "SELECT * FROM Exam"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        exams = cursor.fetchall()

        result = [
            {
                "ExamID": exam[0],
                "UnitID": exam[1],
                "ExamName": exam[2],
                "MaxMarks": exam[3]
            }
            for exam in exams
        ]
        return {"exams": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.post("/api/exam/add")
async def add_exam(exam: Exam):
    query = """
        INSERT INTO Exam (ExamID, UnitID, ExamName, MaxMarks)
        VALUES (%s, %s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (exam.ExamID, exam.UnitID, exam.ExamName, exam.MaxMarks))
        connection.commit()
        return {"message": "Exam added successfully", "ExamID": exam.ExamID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/exam/update/{exam_id}")
async def update_exam(exam_id: int, exam: Exam):
    query = """
        UPDATE Exam 
        SET UnitID = %s, ExamName = %s, MaxMarks = %s
        WHERE ExamID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (exam.UnitID, exam.ExamName, exam.MaxMarks, exam_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Exam with ID {exam_id} not found")

        return {"message": f"Exam with ID {exam_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.delete("/api/exam/delete/{exam_id}")
async def delete_exam(exam_id: int):
    query = "DELETE FROM Exam WHERE ExamID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (exam_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Exam with ID {exam_id} not found")

        return {"message": f"Exam with ID {exam_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

            class ExamSchedule(BaseModel):
                ExamScheduleID: int
                ExamID: int
                ExamDate: str
                ExamTime: str
                VenueID: int


            @app.get("/api/exam_schedule/all")
            async def get_all_exam_schedules():
                query = "SELECT * FROM ExamSchedule"
                try:
                    connection = database.get_connection()
                    cursor = connection.cursor()
                    cursor.execute(query)
                    exam_schedules = cursor.fetchall()

                    result = [
                        {
                            "ExamScheduleID": exam[0],
                            "ExamID": exam[1],
                            "ExamDate": str(exam[2]),
                            "ExamTime": str(exam[3]),
                            "VenueID": exam[4]
                        }
                        for exam in exam_schedules
                    ]
                    return {"exam_schedules": result}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
                finally:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()


            @app.post("/api/exam_schedule/add")
            async def add_exam_schedule(exam_schedule: ExamSchedule):
                query = """
                    INSERT INTO ExamSchedule (ExamScheduleID, ExamID, ExamDate, ExamTime, VenueID)
                    VALUES (%s, %s, %s, %s, %s)
                """
                try:
                    connection = database.get_connection()
                    cursor = connection.cursor()
                    cursor.execute(
                        query,
                        (exam_schedule.ExamScheduleID, exam_schedule.ExamID, exam_schedule.ExamDate,
                         exam_schedule.ExamTime, exam_schedule.VenueID)
                    )
                    connection.commit()
                    return {"message": "Exam Schedule added successfully",
                            "ExamScheduleID": exam_schedule.ExamScheduleID}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
                finally:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()


            @app.put("/api/exam_schedule/update/{exam_schedule_id}")
            async def update_exam_schedule(exam_schedule_id: int, exam_schedule: ExamSchedule):
                query = """
                    UPDATE ExamSchedule 
                    SET ExamID = %s, ExamDate = %s, ExamTime = %s, VenueID = %s
                    WHERE ExamScheduleID = %s
                """
                try:
                    connection = database.get_connection()
                    cursor = connection.cursor()
                    cursor.execute(
                        query,
                        (exam_schedule.ExamID, exam_schedule.ExamDate, exam_schedule.ExamTime,
                         exam_schedule.VenueID, exam_schedule_id)
                    )
                    connection.commit()

                    if cursor.rowcount == 0:
                        raise HTTPException(status_code=404,
                                            detail=f"ExamSchedule with ID {exam_schedule_id} not found")

                    return {"message": f"ExamSchedule with ID {exam_schedule_id} updated successfully"}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
                finally:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()


            @app.delete("/api/exam_schedule/delete/{exam_schedule_id}")
            async def delete_exam_schedule(exam_schedule_id: int):
                query = "DELETE FROM ExamSchedule WHERE ExamScheduleID = %s"
                try:
                    connection = database.get_connection()
                    cursor = connection.cursor()
                    cursor.execute(query, (exam_schedule_id,))
                    connection.commit()

                    if cursor.rowcount == 0:
                        raise HTTPException(status_code=404,
                                            detail=f"ExamSchedule with ID {exam_schedule_id} not found")

                    return {"message": f"ExamSchedule with ID {exam_schedule_id} deleted successfully"}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
                finally:
                    if cursor:
                        cursor.close()
                    if connection:
                        connection.close()


class AdmitCard(BaseModel):
    AdmitCardID: int
    ApplicationID: int
    ExamScheduleID: int
    AdmitDate: str



@app.get("/api/admit_card/all")
async def get_all_admit_cards():
    query = "SELECT * FROM AdmitCard"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        admit_cards = cursor.fetchall()

        result = [
            {
                "AdmitCardID": admit[0],
                "ApplicationID": admit[1],
                "ExamScheduleID": admit[2],
                "AdmitDate": str(admit[3])
            }
            for admit in admit_cards
        ]
        return {"admit_cards": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.post("/api/admit_card/add")
async def add_admit_card(admit_card: AdmitCard):
    query = """
        INSERT INTO AdmitCard (AdmitCardID, ApplicationID, ExamScheduleID, AdmitDate)
        VALUES (%s, %s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            query,
            (admit_card.AdmitCardID, admit_card.ApplicationID, admit_card.ExamScheduleID, admit_card.AdmitDate)
        )
        connection.commit()
        return {"message": "Admit Card added successfully", "AdmitCardID": admit_card.AdmitCardID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/admit_card/update/{admit_card_id}")
async def update_admit_card(admit_card_id: int, admit_card: AdmitCard):
    query = """
        UPDATE AdmitCard 
        SET ApplicationID = %s, ExamScheduleID = %s, AdmitDate = %s
        WHERE AdmitCardID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            query,
            (admit_card.ApplicationID, admit_card.ExamScheduleID, admit_card.AdmitDate, admit_card_id)
        )
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"AdmitCard with ID {admit_card_id} not found")

        return {"message": f"AdmitCard with ID {admit_card_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.delete("/api/admit_card/delete/{admit_card_id}")
async def delete_admit_card(admit_card_id: int):
    query = "DELETE FROM AdmitCard WHERE AdmitCardID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (admit_card_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"AdmitCard with ID {admit_card_id} not found")

        return {"message": f"AdmitCard with ID {admit_card_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

class Result(BaseModel):
    ResultID: int
    StudentID: int
    ExamID: int
    Marks: int



@app.post("/api/result/add")
async def add_result(result: Result):
    # Check if Student has given Exam
    check_query = "SELECT * FROM Exam WHERE ExamID = %s"
    insert_query = """
        INSERT INTO Result (ResultID, StudentID, ExamID, Marks)
        VALUES (%s, %s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()

        cursor.execute(check_query, (result.ExamID,))
        exam_exists = cursor.fetchone()

        if not exam_exists:
            raise HTTPException(status_code=400, detail="Student has not given this Exam")

        cursor.execute(
            insert_query,
            (result.ResultID, result.StudentID, result.ExamID, result.Marks)
        )
        connection.commit()
        return {"message": "Result added successfully", "ResultID": result.ResultID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/result/update/{result_id}")
async def update_result(result_id: int, result: Result):
    query = """
        UPDATE Result
        SET StudentID = %s, ExamID = %s, Marks = %s
        WHERE ResultID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (result.StudentID, result.ExamID, result.Marks, result_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Result with ID {result_id} not found")

        return {"message": f"Result with ID {result_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.delete("/api/result/delete/{result_id}")
async def delete_result(result_id: int):
    query = "DELETE FROM Result WHERE ResultID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (result_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Result with ID {result_id} not found")

        return {"message": f"Result with ID {result_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.get("/api/result/highest_mark")
async def get_highest_mark_student():
    query = """
        SELECT s.Name, r.Marks 
        FROM Result r
        JOIN Student s ON r.StudentID = s.StudentID
        ORDER BY r.Marks DESC
        LIMIT 1
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        highest = cursor.fetchone()

        if not highest:
            return {"message": "No results found"}

        return {"Highest_Mark_Student": highest[0], "Marks": highest[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.get("/api/result/lowest_mark")
async def get_lowest_mark_student():
    query = """
        SELECT s.Name, r.Marks 
        FROM Result r
        JOIN Student s ON r.StudentID = s.StudentID
        ORDER BY r.Marks ASC
        LIMIT 1
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        lowest = cursor.fetchone()

        if not lowest:
            return {"message": "No results found"}

        return {"Lowest_Mark_Student": lowest[0], "Marks": lowest[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.get("/api/result/ordered_by_marks")
async def get_students_ordered_by_marks():
    query = """
        SELECT s.Name, r.Marks 
        FROM Result r
        JOIN Student s ON r.StudentID = s.StudentID
        ORDER BY r.Marks DESC
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        students = cursor.fetchall()

        result = [{"Name": student[0], "Marks": student[1]} for student in students]

        return {"Ordered_Students": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

class Unit(BaseModel):
    UnitID: str
    UnitName: str
    MaxCapacity: int



@app.post("/api/unit/add")
async def add_unit(unit: Unit):
    query = """
        INSERT INTO Unit (UnitID, UnitName, MaxCapacity)
        VALUES (%s, %s, %s)
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (unit.UnitID, unit.UnitName, unit.MaxCapacity))
        connection.commit()
        return {"message": "Unit added successfully", "UnitID": unit.UnitID}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



@app.put("/api/unit/update/{unit_id}")
async def update_unit(unit_id: str, unit: Unit):
    query = """
        UPDATE Unit
        SET UnitName = %s, MaxCapacity = %s
        WHERE UnitID = %s
    """
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (unit.UnitName, unit.MaxCapacity, unit_id))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Unit with ID {unit_id} not found")

        return {"message": f"Unit with ID {unit_id} updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.delete("/api/unit/delete/{unit_id}")
async def delete_unit(unit_id: str):
    query = "DELETE FROM Unit WHERE UnitID = %s"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query, (unit_id,))
        connection.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Unit with ID {unit_id} not found")

        return {"message": f"Unit with ID {unit_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.get("/api/unit/show_all")
async def show_all_units():
    query = "SELECT * FROM Unit"
    try:
        connection = database.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        units = cursor.fetchall()

        result = [
            {"UnitID": unit[0], "UnitName": unit[1], "MaxCapacity": unit[2]}
            for unit in units
        ]
        return {"units": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


