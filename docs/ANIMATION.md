# Traces for M3_Pilot

These are intended native-animation traces, not a claim that ProB was run here. For Commit and CancelConfirmed, bind the additional parameter R to pending∖{j} in the pre-state. For Submit, bind T to (pending∖submitted)∖{j} in the pre-state. These values are unique; the remaining guards are proved theorems. All guards and parameter values refer to the shipped source. P is the exact authorization relation after a credential update; choose the value given below. All actions in one event are simultaneous.

## Revocation between Submit and Commit

1. INITIALISATION.
2. Delegate(a=a1, S=CAP, P={u,a1} × CAP).
3. Delegate(a=a2, S={writeCap}, P=({u,a1} × CAP) ∪ {a2 ↦ writeCap}).
4. Reserve(j=req2): used becomes 1, req2 enters pending.
5. Submit(j=req2): req2 enters submitted.
6. Revoke(a=a1, P={u} × CAP): both a1 and a2 lose effective authority.
7. Commit(j=req2) must be disabled by current authorization.
8. CancelConfirmed(j=req2) remains enabled: used becomes 0 and req2 enters cancelled.

## At most one effect

1. Start again from INITIALISATION.
2. Delegate(a=a1, S={readCap}, P=({u} × CAP) ∪ {a1 ↦ readCap}).
3. Reserve(j=req1).
4. Submit(j=req1).
5. Commit(j=req1): effectCount(req1)=1, req1 is committed and no longer pending/submitted. used stays 1.
6. A second Reserve, Submit or Commit on req1 must be disabled. CancelConfirmed on req1 must also be disabled.

## Shared limit across two sibling agents

1. Start again from INITIALISATION.
2. Delegate(a=a1, S=CAP, P={u,a1} × CAP).
3. Delegate(a=a2, S={writeCap}, P=({u,a1} × CAP) ∪ {a2 ↦ writeCap}).
4. Delegate(a=a3, S={readCap}, P=({u,a1} × CAP) ∪ {a2 ↦ writeCap,a3 ↦ readCap}).
5. Reserve(j=req2), then Reserve(j=req3): used=2=budget.
6. Reserve(j=req1) must be disabled, although a1 has the needed read capability.
7. CancelConfirmed(j=req2) reduces used to 1, after which Reserve(j=req1) is enabled.

## Attenuation

After Delegate(a1,{readCap},...), Delegate(a2,{writeCap},...) must be disabled by S⊆scope(parent(a2)). Descendant credentials cannot add a capability absent from their immediate parent even when the root possesses it.
