const express = require("express")
const localtunnel = require("localtunnel")
const yargs = require("yargs")
const app = express()
const argv = yargs
  .usage("Usage: $0 <service> [options]")
  .example("$0 service:8080 -p 4040")
  .demandCommand(1, "Must enter service")
  .alias("p", "port")
  .describe("p", "Port to manage tunnel")
  .alias("h", "help")
  .help("h")
  .argv
const [localhost, localport] = argv._[0].split(":")

var tunnel = null

app.get("/start", async (req, res) => {
  tunnel = await localtunnel({port: localport, local_host: localhost})
  tunnel.on("request", (info) => { console.log(info) })
  tunnel.on("error", (err) => { console.error(err) })
  tunnel.on("close", () => { console.log("Closing tunnel") })
  res.json({status: "started", url: tunnel.url})
})
app.get("/stop", async (req, res) => {
  if (tunnel !== null) {
    tunnel.close()
    res.json({status: "stopped"})
  } else {
    res.json({status: "already stopped"})
  }
  tunnel = null
})
app.get("/status", async (req, res) => {
  res.json({
    host: localhost,
    port: localport,
    mangement: argv.port,
    status: tunnel === null ? "stopped" : "running",
    url: tunnel === null ? null : tunnel.url
  })
})

app.listen(argv.port, () => {
  console.log(`Tunnel to ${localhost}:${localport} running; mangement available on ${argv.port}`)
})
