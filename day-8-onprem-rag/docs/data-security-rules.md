# Data security rules for on-prem AI

The first rule is that data never leaves the building. The model runs on the
company's own servers, on the company's own network, and no request ever
goes to a public API. This is what makes the system safe for sensitive
material, including patented research. A leak is impossible by design when
nothing is transmitted anywhere.

The second rule is role-based access. Only the right people see the right
documents. Access is controlled per document and per team, so a question
from one team can only retrieve passages that team is allowed to see.

The third rule is that every access is logged. Each question, each retrieved
passage, and each answer is recorded with a timestamp. If anyone ever asks
who saw a document and when, the log has the answer.

The fourth rule is that the model itself is open and downloaded once. There
is no vendor API key, no subscription, and no outside party that can read,
retain, or train on the company's data. Updates to the model are reviewed
and versioned, never automatic. The model does not retrain itself from
employee chats. It improves in a controlled way: new documents are added
to the store, and releases are tested before they go live.
