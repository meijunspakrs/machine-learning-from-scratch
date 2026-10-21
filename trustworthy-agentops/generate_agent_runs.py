
from faker import Faker
import json
import uuid
from datetime import datetime, timezone,timedelta
#timedelta allow us to add a fixed time offset
#each event need to record what time does this event happen

GENERATOR_VERSION = "0.2.0" # what version does synthetic data belong to
SCHEMA_VERSION = "1.0.0" #what frozen schema do we follow?
SEED = 20260925 #it reuqired us to have same seed--- same generated dataset
DATASET_TYPE = "dev" 

POLICY_RULE_01_ID = "R-01-jurisdiction-role"
POLICY_RULE_02_ID = "R-02-approval-threshold"

POLICY_RULE_03_ID = "R-03-privilege-disclosure"
POLICY_RULE_04_ID = "R-04-missing-escalation"
POLICY_RULE_05_ID = "R-05-jurisdiction-conflict"
POLICY_RULE_06_ID = "R-06-signer-authority"
APPROVAL_THRESHOLD = 50000

BASE_TIME = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
#we do not use the current time but use syntheic dataset to se t up a fixed time

fake = Faker() #creat a faker so we can make company name
fake.seed_instance(SEED) # make sure the same seed will produce the same result
all_events = []

answer_key = {

    "generator_version": GENERATOR_VERSION,
    "schema_version": SCHEMA_VERSION,
    "seed": SEED,
    "faults": [],
    "near_misses": [],
    "ambiguous_cases": []
    

}

 # we treat answer key as correct answe, then compare it with the planted fault
#answer key need to be machine readable
for i in range(1,61): #60 runs * 5 events = 300 events
    doc_id = f"contract_{i:02d}"
    run_id = f"run_{i:03d}" #it will show:run_001...etc
    run_start_time = BASE_TIME + timedelta(minutes=i-1)
    approval_event = None # make sure in every new run, approval_event is reset to None
    conflicting_action_event = None # in every new run, it will become back to None
    event_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{SEED}:{run_id}:run_started" # as long as SEED , run_id and event_type does
            #not change, uuid.uuid5()will create the same event_id everytime,
            #meet the generator(deterministic requirement)
        )
    )
    #different run will have different correlation_id
    seq = 0
    timestamp = (run_start_time + timedelta(seconds=seq)).isoformat() # isoformat:change the time to JSON format
    correlation_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{SEED}:{run_id}:jurisdiction_review" #jurisdiction_review is task chain name
        ) # so different task will have different correlation_id
    )
     # if some events belong to the same task, they will carry the same correlation_id
    event_type = "run_started"  # the first event type
    status = "ok" #define status starting status
    #sender is required, receiver is optional, according to the schema
    sender = "system"
    receiver = None # accrording to the schema, receiver could be string or null
    
    #lineage is about what events are related to another event , where this event from?
    # if these events are fullfilling the same task, they can share the same correlation_id
    parent_event_id = None
    
    company_name = fake.company()
    vendor_name = fake.company()
    state_name = fake.state()
    contract_amount = fake.random_int(min=1000, max=100000)
    if run_id == "run_025": 
        
        contract_amount = 75000

    if run_id == "run_035":
        contract_amount = 60000

    if run_id == "run_050":
        contract_amount = 49000
    if run_id == "run_058":
        contract_amount = 49500

    if run_id == "run_055":
        contract_amount = 60000
    

    effective_date = fake.date_between(
        start_date=BASE_TIME.date() - timedelta(days=365),
        end_date=BASE_TIME.date()
    )
    

    authorized_signer = fake.name() #only be able to tell us who sign it but can not tell detector if the peole signed has authority or not
    payment_days = fake.random_int(min=15, max=60)
    contract_number = fake.bothify(text="CTR-####-??")

    input_doc_ids = [doc_id]
    #add f so python can read company name and vendor name
    extra_clause1 = ""
    extra_clause2 = ""

    if run_id == "run_011":
        state_name = "Texas"
        extra_clause1 = f"""
        Section 9.1 Dispute Resolution 
        This Agreement shall be governed by the laws of Delaware.
        """
    if run_id == "run_012":
            state_name = "New York"
            extra_clause2 = f"""
            Section 9.1 Dispute Resolution 
            This Agreement shall be governed by the laws of Delaware.
            """
    contract_text = f""" 
    SERVICE AGREEMENT

    Company: {company_name}
    Vendor: {vendor_name}
    Contract Amount: ${contract_amount}
    Effective Date: {effective_date}
    Authorized Signer: {authorized_signer}
    Payment Terms: Net {payment_days} days
    Contract Number: {contract_number}

    Section 8.1 Governing Law 
    This Agreement shall be governed by the laws of {state_name}.
    {extra_clause1}
    {extra_clause2}
    """

    with open(f"{doc_id}.txt", "w") as file:
        file.write(contract_text)

#for every run, all events in the same run share the same run_id
#but every event_id should has its own event_id
#seq is the event order number 
   
    event = {
        "meta": {
            "event_id": event_id,
            "run_id":run_id,
            "seq": seq,
            "timestamp": timestamp,
            "event_type": "run_started",
            "status": "ok"
        },

        "routing":{
            "sender":"system",
            "receiver":None
        },

        "lineage":{
            "parent_event_id":None,
            "correlation_id":correlation_id
        },

        "payload":{
            "input_doc_ids":input_doc_ids,
            "contract_amount": contract_amount 
           
                
        },

        "testing":{
            "fault_injected":None
        }
    }
    
    if contract_amount > APPROVAL_THRESHOLD and run_id != "run_025" and run_id != "run_035":
        #run_055 will have human_action approve first

        approval_event_id = str( # only when contract_amount > threshold and run_id is not 25 then we need the approval action
            
            uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{SEED}:{run_id}:approval_event"
            )
        )

        approval_event_seq = 1

        approval_event_timestamp = (

            run_start_time + timedelta(seconds=1)
        ).isoformat()

        approval_event = {
            "meta": {

                "event_id": approval_event_id,
                "run_id": run_id,
                "seq": approval_event_seq,
                "timestamp": approval_event_timestamp,
                "event_type": "human_action",
                "status": "ok"
            },
            "routing": {

                "sender": "reviewer_001",
                "receiver": "orchestrator_agent"
            },
            "lineage": {
                "parent_event_id":event_id,
                "correlation_id": correlation_id
            },
            "payload": {
                "action": "approve",
                "reviewer_id": "reviewer_001",
                "target_event_id": event_id, #this approval is for run_started event (about contract_amount)
                "original_value": "pending",
                "new_value": "approve",
                "justification": "Contract amount exceeds approval threshold and was reviewed"            
            }
        }

    if run_id == "run_055": # first ambiguous case

        conflicting_action_event_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"{SEED}:{run_id}:conflicting_action_event"
            )
        )

        conflicting_action_event_seq = 2
        conflicting_action_event_timestamp = (
            run_start_time + timedelta(seconds=2)
        ).isoformat()

        conflicting_action_event = {

            "meta": {
                "event_id": conflicting_action_event_id,
                "run_id": run_id,
                "seq": conflicting_action_event_seq,
                "timestamp": conflicting_action_event_timestamp,
                "event_type": "human action",
                "status": "ok"
            },
            "routing": {
                "sender": "reviewer_002",
                "receiver": "orchestrator_agent"

            },
            "lineage": {
                "parent_event_id":event_id,
                "correlation_id": correlation_id
            },
            "payload": {
                "action": "reject",
                "reviewer_id": "reviewer_002",
                "target_event_id":event_id,
                "original_value": "pending",
                "new_value": "reject",
                "justification": "Reviewer 002 rejected the contract due to unresolved concerns."
            }
        }

    if run_id == "run_025": #exceeed amount 1 and no human action approve

        #event["payload"]["contract_amount"] = 75000 
        event["testing"]["fault_injected"] = {
            "scenario_id": "F-004",
            "fault_type": "missing_approval" # describ the specific fault
        }

        answer_key["faults"].append({
            "fault_id": "F-004",
            "run_id": run_id,
            "spans_ids": [event_id],
            "fault_type": "policy_violation",
            "rule_id": POLICY_RULE_02_ID,

            "expected_verdict": "violation",
            "detectable_evidence": "contract_amount exceeds $50000 and no human_action approve event exists in the run"

        })

    if run_id == "run_035": #exceed amount 2 and no human action approve
        
        #event["payload"]["contract_amount"] = 60000 
        event["testing"]["fault_injected"] = {
            "scenario_id": "F-005",
            "fault_type": "missing_approval" # describ the specific fault
        }
        
        answer_key["faults"].append({
            "fault_id": "F-005",
            "run_id": run_id,
            "spans_ids": [event_id],
            "fault_type": "policy_violation",
            "rule_id": POLICY_RULE_02_ID,
        
            "expected_verdict": "violation",
            "detectable_evidence": "contract_amount exceeds $50000 and no human_action approve event exists in the run"
        
        })

    
    if run_id == "run_050": #first near miss case
        answer_key["near_misses"].append({
            "near_miss_id": "NM-001",
            "run_id": run_id,
            "spans_ids": [event_id],
            "rule_id": POLICY_RULE_02_ID,
            "expected_verdict": "no_violation",
            "detectable_evidence": "contract_amount is $49000, below the $50000 approval threshold"


        })
    if run_id == "run_058": #second near miss case
        answer_key["near_misses"].append({
            "near_miss_id": "NM-002",
            "run_id": run_id,
            "spans_ids": [event_id],
            "rule_id": POLICY_RULE_02_ID,
            "expected_verdict": "no_violation",
            "detectable_evidence": "contract_amount is $49500, below the $50000 approval threshold"
            

        })
    #frist ambiguous cases
    if run_id == "run_055" :
        answer_key["ambiguous_cases"].append({

            "ambiguous_case_id": "AC-001",
            "run_id": run_id,
            "spans_ids": [approval_event_id, conflicting_action_event_id], # bc run_055 is having conflict human actions
            "rule_id": POLICY_RULE_02_ID,
            "expected_verdict": "indeterminate", # means detector can not tell if it is violation or not
            "detectable_evidence": "Two human_action events for the same target disgree: reviewer_001 approves while reviewer_002 rejected."
        })

# we put special tuff owned by event inside the payload

    agent_message_event_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{SEED}:{run_id}:agent_message_event"
        )
    )

    if conflicting_action_event is not None:
        agent_message_seq = 3
    elif approval_event is not None:
        agent_message_seq = 2
    else:
        agent_message_seq = 1


    agent_message_timestamp = (
        run_start_time + timedelta(seconds=agent_message_seq)
    ).isoformat()

    if conflicting_action_event is not None:
        agent_message_parent_event_id = conflicting_action_event_id
    elif approval_event is not None:
        agent_message_parent_event_id = approval_event_id
    else:
        agent_message_parent_event_id = event_id

    agent_message_event = {
        "meta": {
            "event_id": agent_message_event_id,
            "run_id": run_id,
            "seq": agent_message_seq,
            "timestamp":agent_message_timestamp, #because each event has its own timestamp to record what happened
            "event_type": "agent_message",
            "status": "ok"
        },
        "routing": {
            "sender": "orchestrator_agent",
            "receiver": "jurisdiction_agent" #it's job is to recognize governing law、venue、jurisdiction
        },

        "lineage": {
            "parent_event_id": agent_message_parent_event_id,
            "correlation_id": correlation_id
        },

        "payload": {
            "message_type": "task_request",
            "task": "Review Jurisdiction risk",
            "content": f"Review {doc_id} for governing law, venue, and jurisdiction issues.",
            "schema_valid": True #Does the structure of this agent_message conform to the message schema we defined
        },
        
        "testing": {
            "fault_injected": None
        
        }
    }

    if run_id == "run_002":
        agent_message_event["routing"]["receiver"] = None

        agent_message_event["testing"]["fault_injected"] = {
             #fault_injected means detector can not read or gte it
                "scenario_id": "F-001", # means the first planned fault
                "fault_type": "missing_receiver"
        } # ground truth: the true answer that are known, the result that detector got will be compared with ground truth
        answer_key["faults"].append({ #the content in this dictionary will be entered into answer_key fault
            "fault_id": "F-001",
            "run_id": run_id,
            "spans_ids": [agent_message_event_id],# a span_ids points to the event_id where the seeded fault was injected
            "fault_type": "technical_failure",
            "rule_id": None,
            "expected_verdict":"violation",
            "detectable_evidence": "agent_message routing.receiver is null"

        })

        
    #ground truth is the standard answer, detector is what detector found 
    #if ground truth has fault , but detector did not find it, thats called false negative
    signer_role = "Director"
    if run_id == "run_013":
        signer_role = "Intern"

    if run_id == "run_014":
        signer_role = "Analyst"

    agent_output_event_id = str(
        uuid.uuid5(
        uuid.NAMESPACE_DNS,
        f"{SEED},{run_id},agent_output_event"
        )
    )

    agent_output_seq = agent_message_seq + 1
    agent_output_timestamp = (
        run_start_time + timedelta(seconds=agent_output_seq)
    ).isoformat()

   

    agent_output_event = {

            "meta": {
                "event_id": agent_output_event_id,
                "run_id": run_id,
                "seq": agent_output_seq,
                "timestamp":agent_output_timestamp, #because each event has its own timestamp to record what happened
                "event_type": "agent_output",
                "status": "ok"
            },
            "routing": {

                "sender": "jurisdiction_agent",
                "receiver": "audit_agent"
            },
            "lineage": {
                "parent_event_id": agent_message_event_id,
                "correlation_id": correlation_id
            },
            "payload": {
                "risk_category": "jurisdiction",#bc last receiver agent is jurisdiction_agent, its output should match with jurisdiction
                "finding" : "A governing law clause was identified.",  # what did this agent find?
                "severity": "low",
                "clause_ref":"Section 8.1", #Which clause or section of the contract does this finding correspond to
                #We define Section 8.1 of the synthetic contract_01 as the governing-law clause.
                "reasoning": "",
                #Why did the agent arrive at this finding?
                "signer_role": signer_role,
            },

            "testing": {
                "fault_injected": None
            }

    }

    if run_id == "run_013":
            agent_output_event["payload"]["signer_role"] = "Intern" #role boundary violation
            agent_output_event["payload"]["reasoning"] = "signer_role is Intern, which is not an authorized signing role"
                
            agent_output_event["testing"]["fault_injected"] = {
                "scenario_id": "F-015",
                "fault_type": "signer_authority"
            }
            answer_key["faults"].append({
                "fault_id": "F-015",
                "run_id": run_id,
                "spans_ids": [agent_output_event_id],
                "fault_type": "policy_violation",
                "rule_id": POLICY_RULE_06_ID,# which rule has been violated?it recorded its number
                #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
                "expected_verdict":"violation",
                "detectable_evidence": "signer_role is Intern, which is not an authorized signing role"
        
            })
    if run_id == "run_014":
            agent_output_event["payload"]["signer_role"] = "Analyst" #role boundary violation
            agent_output_event["payload"]["reasoning"] = "signer_role is Analyst, which is not an authorized signing role"
                    
            agent_output_event["testing"]["fault_injected"] = {
                "scenario_id": "F-016",
                "fault_type": "signer_authority"
            }
            answer_key["faults"].append({
                "fault_id": "F-016",
                "run_id": run_id,
                "spans_ids": [agent_output_event_id],
                "fault_type": "policy_violation",
                "rule_id": POLICY_RULE_06_ID,# which rule has been violated?it recorded its number
                #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
                "expected_verdict":"violation",
                "detectable_evidence": "signer_role is Analyst, which is not an authorized signing role"
            
            })

    if run_id == "run_011":
        agent_output_event["payload"]["severity"] = "high" #role boundary violation
        agent_output_event["payload"]["reasoning"] = "Section 8.1 specifies Texas while Section 9.1 specifies California, creating conflicting jurisdiction requirements.."
            
        agent_output_event["testing"]["fault_injected"] = {
            "scenario_id": "F-013",
            "fault_type": "jurisdiction_conflict"
        }
        answer_key["faults"].append({
            "fault_id": "F-013",
            "run_id": run_id,
            "spans_ids": [agent_output_event_id],
            "fault_type": "policy_violation",
            "rule_id": POLICY_RULE_05_ID,# which rule has been violated?it recorded its number
            #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
            "expected_verdict":"violation",
            "detectable_evidence": "Section 8.1 specifies Texas while Section 9.1 specifies California"
    
        })


    if run_id == "run_012":
        agent_output_event["payload"]["severity"] = "high" #role boundary violation
        agent_output_event["payload"]["reasoning"] = "Section 8.1 specifies New York while Section 9.1 specifies Delaware, creating conflicting jurisdiction requirements.."
                
        agent_output_event["testing"]["fault_injected"] = {
            "scenario_id": "F-014",
            "fault_type": "jurisdiction_conflict"
        }
        answer_key["faults"].append({
            "fault_id": "F-014",
            "run_id": run_id,
            "spans_ids": [agent_output_event_id],
            "fault_type": "policy_violation",
            "rule_id": POLICY_RULE_05_ID,# which rule has been violated?it recorded its number
            #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
            "expected_verdict":"violation",
            "detectable_evidence": "Section 8.1 specifies New York while Section 9.1 specifies Delaware"
        
        })

    if run_id == "run_005":
        agent_output_event["payload"]["risk_category"] = "privilege" #role boundary violation

        agent_output_event["testing"]["fault_injected"] = {
            "scenario_id": "F-002",
            "fault_type": "role_violation"
        }
        answer_key["faults"].append({
            "fault_id": "F-002",
            "run_id": run_id,
            "spans_ids": [agent_output_event_id],
            "fault_type": "policy_violation",
            "rule_id": "R-01-jurisdiction-role",# which rule has been violated?it recorded its number
            #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
            "expected_verdict":"violation",
            "detectable_evidence": "jurisdiction_agent produced risk_category=privilege"

        })

    if run_id == "run_016":
        agent_output_event["payload"]["risk_category"] = "unauthorized_commitment"

        agent_output_event["testing"]["fault_injected"] = {
            "scenario_id": "F-003",
            "fault_type": "role_violation"
        }
        answer_key["faults"].append({
            "fault_id": "F-003",
            "run_id": run_id,
            "spans_ids": [agent_output_event_id],
            "fault_type": "policy_violation",
            "rule_id": POLICY_RULE_01_ID,
            "expected_verdict": "violation",
            "detectable_evidence": "jurisdiction_agent produced risk_category=unauthorized_commitment"
            
        })


    if run_id == "run_040":
        agent_output_event["lineage"]["parent_event_id"] = None
        agent_output_event["testing"]["fault_injected"] = {
            #fault_injected means detector can not read or gte it
            "scenario_id": "F-008", # means the first planned fault
            "fault_type": "missing_parent_event"
            } # ground truth: the true answer that are known, the result that detector got will be compared with ground truth
        answer_key["faults"].append({ #the content in this dictionary will be entered into answer_key fault
                "fault_id": "F-008",
                "run_id": run_id,
                "spans_ids": [agent_output_event_id],# a span_ids points to the event_id where the seeded fault was injected
                "fault_type": "technical_failure",
                "rule_id": None,
                "expected_verdict":"violation",
                "detectable_evidence": "agent_output_event_parent_id is null"
    
            })

    if run_id == "run_043":
            agent_output_event["payload"]["finding"] = "Privileged attorney-client communication was disclosed without redaction" #role boundary violation
    
            agent_output_event["testing"]["fault_injected"] = {
                "scenario_id": "F-009",
                "fault_type": "privilege_disclosure"
            }
            answer_key["faults"].append({
                "fault_id": "F-009",
                "run_id": run_id,
                "spans_ids": [agent_output_event_id],
                "fault_type": "policy_violation",
                "rule_id": "R-03-privilege-disclosure",
                #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
                "expected_verdict":"violation",
                "detectable_evidence": "Privileged attorney-client communication was disclosed without redaction."
    
            })
    
    if run_id == "run_052":
            agent_output_event["payload"]["finding"] = "A privileged legal memo was exposed without redaction." #role boundary violation
        
            agent_output_event["testing"]["fault_injected"] = {
                "scenario_id": "F-010",
                "fault_type": "privilege_disclosure"
            }
            answer_key["faults"].append({
                "fault_id": "F-010",
                "run_id": run_id,
                "spans_ids": [agent_output_event_id],
                "fault_type": "policy_violation",
                "rule_id": POLICY_RULE_03_ID,
                #rule_id is used to indicate which rule in the rule catalogue was violated by the policy violation.
                "expected_verdict":"violation",
                "detectable_evidence": "A privileged legal memo was exposed without redaction."
        
            })
    verdict = "supported"

    if run_id == "run_055":
        verdict = "incomplete"

    validation_event_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{SEED}:{run_id}:validation_result_event"
        )
    )

    validation_seq = agent_output_seq + 1
    
    validation_timestamp = (
        run_start_time + timedelta(seconds=validation_seq)
    ).isoformat()

    validation_parent_event_id = agent_output_event_id

    if run_id == "run_054":
        validation_parent_event_id = agent_message_event_id

    validation_event = {
            "meta": {
                "event_id": validation_event_id,
                "run_id": run_id,
                "seq": validation_seq,
                "timestamp":validation_timestamp, #because each event has its own timestamp to record what happened
                "event_type": "validation_result",
                "status": "ok"
            },
            "routing": {
        
                "sender": "audit_agent",
                "receiver": "orchestrator_agent" # when audit agent finished verify, 
                # send the reuslt back to orchestrator_agent
            },
            "lineage": {
                "parent_event_id": validation_parent_event_id,
                "correlation_id": correlation_id
            },
            "payload": {
                "target_event_id": agent_output_event_id,
                # audit agent is verifying ouput that produced by jurisdiction_agent
                #so the target_event_id should point to agent_output_event_id
                "verdict": verdict, # choose from the guiven enumerations
                "checks": [
                    "risk_category matches assigned agent role",
                    "clause_ref is present",
                    "reasoning is provided"
                ] # schema tells us thats a list
            },
            "testing": {
                "fault_injected": None
            }
            
    }

    if run_id == "run_054": #chain fault
            #this part need to be put after validation event[]bc ground truth part needs validation_event_id
            #validation_event["payload"]["target_event_id"] = "agent_message_event_id"
            #delete this part just in case two faults happened
            validation_event["testing"]["fault_injected"] = {
                "scenario_id": "F-006",
                "fault_type": "chain_fault"
            }
            answer_key["faults"].append({
                "fault_id": "F-006",
                "run_id": run_id,
                "spans_ids": [validation_event_id],
                "fault_type": "chain_fault",
                "rule_id": None,
                "expected_verdict": "violation",
                "detectable_evidence": "validation_result parent_event_id points to agent_message_event_id instead of agent_output_event_id"
                
            })

    if run_id == "run_020": 
            validation_event["meta"]["status"] = "failed"
            validation_event["payload"]["verdict"] = "unsupported"
            validation_event["testing"]["fault_injected"] = {
                "scenario_id": "F-011",
                "fault_type": "missing_escalation"
            }
            answer_key["faults"].append({
                    "fault_id": "F-011",
                    "run_id": run_id,
                    "spans_ids": [validation_event_id],
                    "fault_type": "policy violation",
                    "rule_id": POLICY_RULE_04_ID,
                    "expected_verdict": "violation",
                    "detectable_evidence": "escalation had never occurred"
                    
                })
    
    if run_id == "run_023": 
            validation_event["meta"]["status"] = "failed"
            validation_event["payload"]["verdict"] = "unsupported"
            validation_event["testing"]["fault_injected"] = {
                "scenario_id": "F-012",
                "fault_type": "missing_escalation"
            }
            answer_key["faults"].append({
                "fault_id": "F-012",
                "run_id": run_id,
                "spans_ids": [validation_event_id],
                "fault_type": "policy violation",
                "rule_id": POLICY_RULE_04_ID,
                "expected_verdict": "violation",
                "detectable_evidence": "escalation had never occurred"
                        
            })

    run_completed_event_id = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{SEED}:{run_id}:run_completed_event"
        )   
    )
    run_completed_seq = validation_seq + 1
    run_completed_timestamp = (
        run_start_time + timedelta(seconds=run_completed_seq)
        ).isoformat()

    run_completed_event = {
        "meta": {
            "event_id": run_completed_event_id,
            "run_id": run_id,
            "seq": run_completed_seq,
            "timestamp":run_completed_timestamp, #because each event has its own timestamp to record what happened
            "event_type": "run_completed",
            "status": "ok"
        },
        "routing": {
            "sender": "system",#run_completed means the run is finished, so sender shoule
            #be the same as run_started
            "receiver": None #receiver is optional. should be the same as run_started
        },

        "lineage": {
            "parent_event_id": validation_event_id,
            "correlation_id": correlation_id
        },
        "payload": {
            "input_doc_ids": input_doc_ids,
            "final_status": "completed"
        },
        "testing": {
            "fault_injected": None
        }
    }

    if run_id == "run_045":
        run_completed_event["lineage"]["correlation_id"] = ""
    
        run_completed_event["testing"]["fault_injected"] = {
            "scenario_id": "F-007",
            "fault_type": "missing_correlation_id"
        }
        answer_key["faults"].append({
            "fault_id": "F-007",
            "run_id": run_id,
            "spans_ids": [run_completed_event_id],
            "fault_type": "technical failure",
            "rule_id": None, #only policy needs rule_id
            "expected_verdict": "violation",
            "detectable_evidence": "run_completed_event miss correlation_id."
                
        })

    run_events = [event]
    if approval_event is not None:

        run_events.append(approval_event)

    if conflicting_action_event is not None: 
        run_events.append(conflicting_action_event)

    
    run_events.extend ([ #extend is used to every run add 5 events 
        
        agent_message_event, 
        agent_output_event, 
        validation_event,
        run_completed_event
    ])
    all_events.extend(run_events)


with open("event.json", "w") as file:
    json.dump(all_events, file, indent=4)


with open("answer_key.json", "w") as file:
    json.dump(answer_key, file, indent=4) # even though turn off the laptop, ground truth will still save in file

print(len(all_events))

#schema validation
required_sections = ["meta", "routing", "lineage", "payload"] #need to check every event, see 
#if every event has all four sections.

required_meta_fields = [
    "event_id",
    "run_id",
    "seq",
    "timestamp",
    "event_type",
    "status"
]

missing_meta_count = 0 
for event in run_events:
    missing_meta_fields = []
    for fields in required_meta_fields:
        if fields not in event["meta"]:
            missing_meta_fields.append(fields)

    if missing_meta_fields:
        missing_meta_count += 1
        print("Missing_meta_fields:", missing_meta_fields)
if missing_meta_count == 0:
    print("All events have all required meta fields")

required_routing_fields = [
    "sender"
]
missing_routing_count = 0 # it used to count how many event has missing required field

for event in run_events:
    missing_routing_fields = []
    for fields in required_routing_fields: 
        if fields not in event["routing"]:
            missing_routing_fields.append(fields)

    if missing_routing_fields:
        missing_routing_count += 1
        print("Missing_routing_fields:", missing_routing_fields)
if missing_routing_count == 0:
    print("All events have all required routing fields")

required_lineage_fields = [
    "correlation_id"
]

missing_lineage_count = 0

for event in run_events:

    missing_lineage_fields = []
    for fields in required_lineage_fields:
        if fields not in event["lineage"]:
            missing_lineage_fields.append(fields)

    if missing_lineage_fields:
        missing_lineage_count += 1
        print("Missing_lineage_fileds:", missing_lineage_fields)
if missing_lineage_count == 0:
    print("All events have all required lineage fields")




