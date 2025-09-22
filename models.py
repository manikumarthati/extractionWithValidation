from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    current_step = db.Column(db.Integer, default=1)  # 1, 2, or 3
    is_completed = db.Column(db.Boolean, default=False)
    
    # Processing results for each step
    step1_result = db.Column(db.Text)  # Structure classification JSON
    step2_result = db.Column(db.Text)  # Field identification JSON
    step3_result = db.Column(db.Text)  # Final extracted data JSON
    
    def set_step_result(self, step, result):
        if step == 1:
            self.step1_result = json.dumps(result)
        elif step == 2:
            self.step2_result = json.dumps(result)
        elif step == 3:
            self.step3_result = json.dumps(result)
    
    def get_step_result(self, step):
        if step == 1 and self.step1_result:
            return json.loads(self.step1_result)
        elif step == 2 and self.step2_result:
            return json.loads(self.step2_result)
        elif step == 3 and self.step3_result:
            return json.loads(self.step3_result)
        return None