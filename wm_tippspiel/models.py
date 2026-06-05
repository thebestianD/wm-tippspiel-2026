from datetime import datetime, timezone
from . import db


class Team(db.Model):
    __tablename__ = "teams"
    code = db.Column(db.String(8), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    group_id = db.Column(db.String(1), nullable=False, index=True)
    group_pos = db.Column(db.Integer, nullable=False)
    fifa_rank = db.Column(db.Integer, nullable=False, default=999)


class Match(db.Model):
    __tablename__ = "matches"
    match_no = db.Column(db.Integer, primary_key=True)
    phase = db.Column(db.String(20), nullable=False)  # group, r32, r16, qf, sf, third, final
    group_id = db.Column(db.String(1), nullable=True)
    home_ref = db.Column(db.String(32), nullable=True)
    away_ref = db.Column(db.String(32), nullable=True)
    home_team_code = db.Column(db.String(8), db.ForeignKey("teams.code"), nullable=True)
    away_team_code = db.Column(db.String(8), db.ForeignKey("teams.code"), nullable=True)

    home_team = db.relationship("Team", foreign_keys=[home_team_code])
    away_team = db.relationship("Team", foreign_keys=[away_team_code])


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Prediction(db.Model):
    __tablename__ = "predictions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    match_no = db.Column(db.Integer, nullable=False, index=True)
    home_goals = db.Column(db.Integer, nullable=True)
    away_goals = db.Column(db.Integer, nullable=True)
    winner_code = db.Column(db.String(8), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint("user_id", "match_no", name="uq_prediction_user_match"),)


class ActualResult(db.Model):
    __tablename__ = "actual_results"
    id = db.Column(db.Integer, primary_key=True)
    match_no = db.Column(db.Integer, unique=True, nullable=False, index=True)
    home_goals = db.Column(db.Integer, nullable=True)
    away_goals = db.Column(db.Integer, nullable=True)
    winner_code = db.Column(db.String(8), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class GroupOverride(db.Model):
    __tablename__ = "group_overrides"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(1), nullable=False, index=True)
    team_code = db.Column(db.String(8), nullable=False)
    forced_rank = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(250), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    __table_args__ = (db.UniqueConstraint("group_id", "team_code", name="uq_group_override_team"),)


class Setting(db.Model):
    __tablename__ = "settings"
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False)


class AuditLog(db.Model):
    __tablename__ = "audit_log"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(80), nullable=False)
    details = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
