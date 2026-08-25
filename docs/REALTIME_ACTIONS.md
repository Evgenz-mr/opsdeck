# Realtime action status

OpsDeck uses Server-Sent Events for execution progress because operations are server-to-client streams and do not require a full WebSocket channel.

Expected events:

```json
{"target":"vmselect-01","state":"running","message":"certificate update started"}
{"target":"vmselect-01","state":"success","terminal":false}
{"state":"success","terminal":true}
```

The action runner can publish connect, precheck, running, postcheck, success and failure events to the execution bus.
