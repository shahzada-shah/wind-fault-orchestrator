# Turbine State Management

## 📊 Turbine States Overview

The system uses six real-world turbine operational states that reflect actual field operations.

### State Definitions

| State | Description | Trigger Condition |
|-------|-------------|-------------------|
| **Online** | Turbine operating normally | Reset action, normal operation restored |
| **Impacted (Derated)** | Operating with reduced capacity | Manual inspection needed, minor issues |
| **Available** | Online but not performing optimally | Temperature related issues, wind speed issues |
| **Stopped** | Manual shutdown or load shutdown | Snooze action, manual stop operation |
| **Repair** | Requires maintenance intervention | Escalation action, critical faults |
| **Netcom** | Communication loss (shows last known state) | Network/communication failure |

---

## 🔄 State Transitions Based on Actions

### Automatic State Transitions

The rules engine automatically updates turbine states based on alarm analysis and recommended actions:

#### **ESCALATE → Repair**
```
Trigger: Critical issues requiring manual intervention
Examples:
- Non-resettable alarms
- Oscillation detected (same fault twice in 10 min)
- High frequency (≥4 in 24h or ≥8 in 7d)
- Critical alarm codes

Result: Turbine state → "Repair"
```

#### **WAIT_COOL_DOWN → Available**
```
Trigger: Temperature-related issues
Examples:
- Temperature >75°C for critical codes
- Codes: EM_83, TEMP_HIGH, GEARBOX_OVERHEAT, GEARBOX_TEMP_HIGH

Result: Turbine state → "Available"
Meaning: Online but not performing optimally due to temperature
```

#### **RESET → Online**
```
Trigger: Conditions allow automatic reset
Examples:
- Resettable alarm
- No oscillation detected
- Frequency within acceptable limits
- Temperature within normal range

Result: Turbine state → "Online"
```

#### **SNOOZE → Stopped**
```
Trigger: Temporary shutdown required
Examples:
- Scheduled maintenance
- Load shutdown
- Manual stop operation

Result: Turbine state → "Stopped"
```

#### **MANUAL_INSPECTION → Impacted (Derated)**
```
Trigger: Requires inspection but can continue operating
Examples:
- Minor vibrations
- Yaw errors
- Sensor calibration issues

Result: Turbine state → "Impacted (Derated)"
```

---

## 📋 Special Case: Derated Codes

Certain alarm codes automatically set the turbine to **Impacted (Derated)** even if the action is RESET:

```python
Derated Codes:
- YAW_ERROR: Yaw alignment issues
- LOW_WIND_SPEED: Insufficient wind
- MINOR_VIBRATION: Small vibration detected
```

**Logic**: These conditions allow operation but with reduced performance.

---

## 🔍 State Transition Examples

### Example 1: High Temperature Event
```
Initial State: Online
Alarm: EM_83 with temperature 82.5°C
Analysis: Temperature exceeds 75°C threshold
Action: WAIT_COOL_DOWN
New State: Available
Rationale: "Temperature 82.5°C exceeds threshold 75.0°C. Wait for cool-down."
```

### Example 2: Oscillating Fault
```
Initial State: Online
Alarm 1: GENERATOR_VIBRATION at 10:00
Action: RESET (no previous occurrences)
State: Online

Alarm 2: GENERATOR_VIBRATION at 10:05 (5 minutes later)
Analysis: Same code within 10 minutes
Action: ESCALATE
New State: Repair
Rationale: "Oscillation detected: Same fault code appeared twice within 10 minutes."
```

### Example 3: Frequency Escalation
```
Alarm History (24 hours):
- 10:00 - PITCH_SYSTEM_FAULT
- 14:00 - PITCH_SYSTEM_FAULT
- 18:00 - PITCH_SYSTEM_FAULT
- 22:00 - PITCH_SYSTEM_FAULT (4th occurrence)

Analysis: ≥4 occurrences in 24h
Action: ESCALATE
New State: Repair
Rationale: "High frequency: 4 occurrences in last 24 hours (threshold: 4)."
```

### Example 4: Minor Issue (Derated)
```
Initial State: Online
Alarm: YAW_ERROR
Analysis: Resettable, no oscillation, normal frequency
Action: RESET
Override: Check derated_codes list
New State: Impacted (Derated)
Reason: Yaw errors allow operation but with reduced efficiency
```

---

## 🎯 State Management API

### View Current Turbine State
```bash
GET /api/v1/turbines/{turbine_id}

Response:
{
  "id": 1,
  "turbine_id": "FR-101",
  "name": "France Turbine 101",
  "state": "Available",
  "last_state_change": "2025-11-10T14:20:00.268Z"
}
```

### Manual State Override
```bash
PATCH /api/v1/turbines/{turbine_id}
Content-Type: application/json

{
  "state": "Stopped"
}
```

**Note**: Manual overrides should be used carefully as they bypass the rules engine.

---

## 📊 State Analytics

### View State Distribution
```bash
GET /api/v1/analytics/turbines/troubled

# Shows turbines grouped by alarm counts
# High alarm count often correlates with Repair/Available states
```

### Track State Changes
Monitor `last_state_change` field to track:
- How often states change
- Time in each state
- Patterns of state transitions

---

## 🔧 Integration with Monitoring

### Real-Time State Monitoring

```python
# Example: Check all turbines in Repair state
GET /api/v1/turbines?state=Repair

# Monitor state transitions
SELECT turbine_id, state, last_state_change 
FROM turbines 
WHERE last_state_change > NOW() - INTERVAL '1 hour'
ORDER BY last_state_change DESC;
```

### Alert Triggers

**Recommended Alert Thresholds:**
- **Repair**: Immediate notification (critical)
- **Available**: Monitor for >2 hours (warning)
- **Impacted (Derated)**: Track efficiency metrics
- **Stopped**: Verify if scheduled maintenance
- **Netcom**: Check communication systems immediately

---

## 🚨 Communication Loss Handling (Netcom)

**Special State: Netcom**
- Indicates loss of communication with turbine
- Shows the last known state before communication loss
- Requires separate monitoring system integration

**Implementation Note**: Currently not automatically set by the rules engine. Requires external network monitoring to detect communication failures and manually update state to Netcom.

**Future Enhancement**:
```python
# Add heartbeat monitoring
if time_since_last_communication > threshold:
    turbine.state = TurbineState.NETCOM
```

---

## 📖 Decision Flow Summary

```
Alarm Received
    ↓
Rules Engine Analysis
    ├─ Not resettable? → ESCALATE → Repair
    ├─ Oscillation? → ESCALATE → Repair
    ├─ High frequency? → ESCALATE → Repair
    ├─ Temp >75°C? → WAIT_COOL_DOWN → Available
    ├─ Derated code? → RESET → Impacted (Derated)
    └─ Normal? → RESET → Online
```

---

## 🎓 Best Practices

1. **Monitor State Transitions**: Track how long turbines stay in each state
2. **Analyze Patterns**: Frequent transitions may indicate systemic issues
3. **Manual Overrides**: Document reasons for manual state changes
4. **Available vs Impacted**: 
   - Available = Temporary condition (temperature, wind)
   - Impacted = Ongoing reduced performance
5. **Repair State**: Should trigger immediate work order creation
6. **Netcom State**: Requires network/communication team involvement

---

## 📈 Reporting & KPIs

### Key Metrics by State

- **Online**: Target uptime percentage
- **Available**: Duration and frequency (efficiency metric)
- **Impacted (Derated)**: Production loss calculation
- **Stopped**: Planned vs unplanned downtime
- **Repair**: MTTR (Mean Time To Repair)
- **Netcom**: Communication availability %

---

## 🔮 Future Enhancements

1. **Predictive State Transitions**: ML-based prediction of state changes
2. **State Transition Logging**: Detailed audit trail of all state changes
3. **Automated Netcom Detection**: Integration with SCADA systems
4. **State-Based Workflows**: Automatic work order creation per state
5. **Performance Tracking**: KPIs per state duration

---

**Last Updated**: 2025-11-10  
**Version**: 1.0  
**Status**: Production Ready

