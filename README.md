# Blockchain byte format
```text
Block [82 + (14 + 34m + 12n + 558p)q]:
- prev_id (raw) [32]
- tx_root (raw) [32]
- time (long long) [8]
- nonce (long long) [8]
- tx_c (unsigned short) [2]
- *tx->tx_c (Tx) []

Tx [14 + 34m + 12n + 558p]:
- time (long long) [8]
- in_c (unsigned short) [2]
- *in->in_c (TxIn) []
- out_c (unsigned short) [2]
- *out->out_c (TxOut) []
- sig_c (unsigned short) [2]
- *sig->sig_c (TxSig) []

TxIn [34]:
- tx_id (raw) [32]
- out_i (unsigned short) [2]

TxOut [12]:
- addr (raw) [8]
- amt (float) [4]

TxSig [558]:
- scr (raw) [526]
- sig (raw) [32]
```