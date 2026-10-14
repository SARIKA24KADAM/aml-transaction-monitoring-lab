# Data dictionary

The project expects AMLSim transaction log columns. The simulator's documented transaction log includes `step,type,amount,nameOrig,oldbalanceOrig,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isSAR,alertID`.

| Field | Meaning | Project handling |
|---|---|---|
| `step` | Simulation time step | Chronological ordering and monitoring group |
| `type` | Transaction type | Segment feature and model input |
| `amount` | Transaction value | Model input and exposure summary |
| `nameOrig` | Originating account ID | Graph link and historical feature partition; excluded from model input |
| `nameDest` | Receiving account ID | Graph link and receiver-history join; excluded from model input |
| `oldbalanceOrig` | Originator balance before event | Candidate model input |
| `oldbalanceDest` | Recipient balance before event | Candidate model input |
| `newbalanceOrig`, `newbalanceDest` | Balances after event | Excluded from model inputs as post-event fields |
| `isSAR` | Simulator-generated SAR-pattern label | Target/evaluation label only |
| `alertID` | Simulator alert/pattern identifier | Retained for review context; excluded from model input |

Column definitions and exact files may vary across AMLSim sample versions. Inspect the CSV header and adapt the preparation mapping if needed.
