# Latitude 10

> Latitude 10 is a software consulting studio. Send us a brief and we build it, by the hour, the day or the month: background coding agents do the work in parallel, and a senior engineer reviews every change. We also build and run EarningsLens, an API platform for AI agents, agent kits and the Coati iPhone app.

## About

- Founder: Jorge Ortega, a senior software engineer with 18 years of experience building SaaS in Costa Rica, the United States and Germany. LinkedIn: https://www.linkedin.com/in/jorgeortega/ · GitHub: https://github.com/jorgeortega
- Company: October Moon LLC, a Wyoming limited liability company. LinkedIn: https://www.linkedin.com/company/latitude10/
- Company page: https://latitude10.tech/company
- Website: https://latitude10.tech (not related to other companies or products named Latitude)

## Hire us

Latitude 10 builds software for clients. Send a brief at https://latitude10.tech/start (six short steps, files, and an NDA request if you want one); you get a private link to follow it.

- By the hour: $60 an hour. A fix, a review, an integration or a second pair of eyes on your code.
- By the day: $480 a day. A feature, a prototype or a focused sprint that needs whole days.
- By the month: $9,600 a month. A product built over months, with us as your development team.

Prices are in US dollars, excluding taxes. Hourly work has a one-hour minimum and is billed in whole hours. The monthly rate is a full-time month of about 20 working days. Pricing: https://latitude10.tech/pricing

How a project works:

1. Brief: Six short steps at /start. Attach designs and specs, and ask for an NDA first if you need one.
2. Scope: We read every brief ourselves, ask what’s missing, and send a proposal with the scope, the rate and the dates.
3. Sign: An NDA, a master services agreement and a statement of work, signed online with a code sent to your email.
4. Build: Background agents work on the tasks in parallel, each in its own sandbox. A senior engineer reviews every change.
5. Deliver: Every change reaches you as a pull request in your repository, and each invoice comes with a summary of the work and the time.

We build with Open-Inspect (https://github.com/open-inspect/background-agents), an open-source system of background coding agents, and a senior engineer reviews every change.

Agents can send a brief for their user (after showing it to them and getting their yes): the MCP tool `request_project` on https://latitude10.tech/mcp, or `POST https://latitude10.tech/api/requests` with the brief as JSON (the fields of the form at /start: name, email, requesterKind, country, objective, projectType, deadlineKind, consent: true, and any others). Files go through the form.

## What we built (proof of what we can build)

- [EarningsLens](https://earningslens.latitude10.tech): Any US company’s latest earnings release, read in plain words, with every figure shown where the release printed it. It shows: A data product over messy documents: a model reads each release into checked figures, graded against the company’s own XBRL, served as an app and a public API.
- [The API platform](https://latitude10.tech/platform): One OpenAPI document becomes an API reference, docs, SDKs, an API client and a hosted MCP server for AI agents. It shows: A multi-tenant SaaS: workspaces, single sign-on, roles, an audit log, Stripe billing and hosted MCP servers on Cloudflare.
- [Agent kits](https://latitude10.tech/platform/mcp/self-host): Agentify and the agent kits for 7 stacks: Node.js, Python, .NET, Java, Ruby, PHP, Scala. It shows: Production libraries in several languages, each released with its tests and a live demo API.
- [Coati](https://latitude10.tech/coati): The control room for the MCP servers and APIs your AI agents call. Connect in seconds, see what an agent sees, and know the moment it breaks. It shows: An iPhone app on the App Store, with a subscription and its own server.
- [Open source](https://github.com/jorgeortega/openapi-agent-check): openapi-agent-check and openapi-agentify, published on npm under the MIT license. It shows: Developer tools other people install: a command-line checker and a middleware library, documented and versioned.

## Platform

Latitude 10 makes APIs work with AI agents: it scores your OpenAPI document, fixes what stops agents, and serves it as a hosted MCP server behind keys or your own sign-in. A registry, reference, docs and SDKs are included. It’s built by Jorge Ortega at October Moon LLC.

One OpenAPI spec as the source of truth, and the API reference, docs, SDKs, API client and MCP server made from it. What works today is marked available; the rest is planned and can't be used or bought yet.

- Registry: available. Every version of your OpenAPI spec, scored and checked in your CI. https://latitude10.tech/platform/registry
- API Reference: available. An interactive reference made from your spec, hosted or embedded. https://latitude10.tech/platform/reference
- Docs: available. Guides beside the reference, synced from Git, readable by agents. https://latitude10.tech/platform/docs
- SDK Generator: available. Typed TypeScript and Python SDKs for your CI, under the MIT licence. https://latitude10.tech/platform/sdks
- API Client: available. Try any endpoint from the browser, and share the requests that matter. https://latitude10.tech/platform/api-client
- Agentify: available. An MCP server from your spec, hosted or self-hosted. https://latitude10.tech/platform/mcp

## Plans

A plan gets a price the day everything it launches with works; no money is taken for a planned plan. See https://latitude10.tech/platform/pricing

- Free (Individual developers and small projects): $0.
  Agent readiness check for any OpenAPI spec, in your browser (available); The readiness check as an MCP server (available); openapi-agent-check, the open-source CLI (MIT) (available); Agent Payments Sandbox (available); Guide to publishing your MCP server (available); A hosted project for one API (available); Registry: every version of your OpenAPI spec, scored and validated (available); Breaking-change diff between versions (available); Readiness gate in your CI before tools are generated (available); Hosted, interactive API reference (available); Embeddable API reference for your own site (available); Hosted MCP server made from your spec (available); API client and playground in the browser (available); Hosted docs and guides, synced from Git (available); llms.txt, llms-full.txt and Markdown for every page (available); A docs MCP server for every site (available).
- Pro (Startups and engineering teams): $150 a month, or $125 a month, billed annually.
  A hosted project for one API (available); Team editors and access controls (available); Registry: every version of your OpenAPI spec, scored and validated (available); Breaking-change diff between versions (available); Readiness gate in your CI before tools are generated (available); Hosted, interactive API reference (available); Hosted docs and guides, synced from Git (available); Custom domain (available); llms.txt, llms-full.txt and Markdown for every page (available); A docs MCP server for every site (available); Hosted MCP server made from your spec (available); OAuth for MCP in front of your own identity provider (available); Typed SDKs, built and published from your CI (available); Monthly and annual billing (available); A preview for every branch (available); Embeddable API reference for your own site (available); Tool allow lists per key (available); Agent analytics: which agents call which tools (available); Generated SDK code under the MIT licence (available); API client and playground in the browser (available); Shared request collections for your team (available); Python SDKs, built and published from your CI (available).
- Business (Growing SaaS companies and larger engineering teams): $600 a month, or $500 a month, billed annually.
  SSO (OIDC) and role-based access (available); Audit log (available); Tool allow lists per key (available); Agent analytics: which agents call which tools (available); A preview for every branch (available); Monthly and annual billing (available); Python SDKs, built and published from your CI (available).
- Enterprise (Regulated businesses and complex API estates): Custom.
  SSO (OIDC) and role-based access (available); Audit log (available); SLA and dedicated support (available).

## Questions

### What is Latitude 10?

Latitude 10 is a software consulting studio. Send us a brief and we build it, by the hour, the day or the month: background coding agents do the work in parallel, and a senior engineer reviews every change. We also build and run EarningsLens, an API platform for AI agents, agent kits and the Coati iPhone app.

### Who does the work?

Jorge Ortega, a senior software engineer with 18 years of experience building SaaS in Costa Rica, the United States and Germany, with background coding agents. He scopes every project, reviews every change and is your contact from the brief to delivery.

### What does it cost?

$60 an hour, $480 a day, $9,600 a month. Prices are in US dollars, excluding taxes. Hourly work has a one-hour minimum and is billed in whole hours. The monthly rate is a full-time month of about 20 working days. The statement of work for each project sets the rate, the scope and the dates before any work starts.

### What can you build?

Web apps, APIs, AI agents and MCP servers, data products and iPhone apps: our own products show each kind. We work in Node.js, Python, .NET, Java, Ruby, PHP and Scala, among others, or in the stack you already use.

### How do you use AI agents?

We build with Open-Inspect, an open-source system of background coding agents. Agents work on independent tasks in parallel, each in its own sandbox, and nothing reaches you until a senior engineer has reviewed it as a pull request.

### Do you sign an NDA?

Yes. Ask for one in your brief and we send our mutual NDA to sign online before you share anything confidential.

### Who owns the code?

You do, once the work is paid in full. It runs on your infrastructure, in your repository. The kit code inside it stays ours and is licensed to you, for good, for that project.

### How do I start?

Send a brief at latitude10.tech/start: six short steps, your files, and an NDA request if you want one. You get a private link to follow it, and we reply by email.

## How agents buy

The kits can be bought by AI agents directly, with USDC over the x402 protocol (Base or Solana) or Bitcoin over Lightning (L402): no account, no checkout page.

1. `GET` a product URL below. The unpaid response is HTTP 402 carrying every way to pay:
   - x402 v1: the JSON body (`accepts[]`), USDC on Base
   - x402 v2: the `PAYMENT-REQUIRED` header, USDC on Base or Solana
   - L402: the `WWW-Authenticate: L402 macaroon="…", invoice="…"` header, a Lightning invoice
2. Pay and retry the same URL: x402 v1 with `X-PAYMENT`, x402 v2 with `PAYMENT-SIGNATURE` (any x402 client, e.g. `@x402/fetch`), or L402 with `Authorization: L402 <macaroon>:<preimage>`.
3. The paid response contains the product: a personal, expiring download link.

Agents that speak MCP can do the same through the MCP server at https://latitude10.tech/mcp (Streamable HTTP; tools: `list_products`, `get_product`, `buy_product`, `check_agent_readiness`, `request_project`). `buy_product` without a payment returns the x402 v2 requirements; an x402 MCP client (e.g. `@x402/mcp`) pays and retries automatically.

A step-by-step guide with diagrams, for people and agents: https://latitude10.tech/products/agent-payments

## Agent-readiness check

How well AI agents will use an API, scored 0–100 from its OpenAPI 3.0 or 3.1 spec with the Agentify API kit's rules (the same score as `npx agentify check`): operationIds, summaries, descriptions, parameters, enums, examples, JSON bodies, response and error schemas, pagination, auth, idempotency and tool count.

- Free: the MCP tool `check_agent_readiness` at https://latitude10.tech/mcp/readiness (Streamable HTTP, no payment tools, no sign-in), also on https://latitude10.tech/mcp. Give it the spec's URL or text; it returns the score, each rule's result and the top findings.
- Full report: `POST https://latitude10.tech/api/readiness/report` with `{"url": "https://…/openapi.json"}` or `{"spec": "<JSON or YAML>"}`, $0.10 over x402 v2 (USDC on Base or Solana). Every finding and a suggested fix per operation. A spec it can't check charges nothing.
- Open source: the same rules and score as a CLI and library, openapi-agent-check (MIT license): https://github.com/jorgeortega/openapi-agent-check and https://www.npmjs.com/package/openapi-agent-check. Run `npx openapi-agent-check openapi.yaml` locally or in CI (`--min 80` fails a build below 80), `--fix` writes a fixed copy of the spec (the rules' fixes, no model call) and `--badge` prints a score badge for a README. Fixes written by a model stay in the Agentify API kit.
- Open source: openapi-agentify (MIT license), the core of the Agentify API kit for Node.js: one middleware for Express, Hono, Fastify or Next.js that serves your API as an MCP server from your OpenAPI spec, in-process through your own routes: https://github.com/jorgeortega/openapi-agentify and https://www.npmjs.com/package/openapi-agentify. Payments, agent keys, OAuth and metering stay in the paid kit.
- Documentation: https://latitude10.tech/agent-readiness (how to connect, the tool's input and output, the rules, limits and data handling).

## The Coati iPhone app

Coati, on the App Store as Coati Dev Tools: The control room for the MCP servers and APIs your AI agents call. Connect in seconds, see what an agent sees, and know the moment it breaks. Download: https://apps.apple.com/us/app/coati-dev-tools/id6823287729. It needs iOS 26 or later and has no account. Help, getting started and common questions: https://latitude10.tech/coati

- Free: paste an MCP URL, an OpenAPI spec, a cURL command or an endpoint and Coati connects; an Agent Readiness Score from 0 to 100 with the top fixes; Test Drive, where a real model tries a task against your server, on-device with Apple Intelligence or with your own Anthropic key; an MCP inspector; and an HTTP workbench.
- Coati Pro, an auto-renewable subscription through Apple: $4.99 a month or $39.99 a year, with a 14-day free trial. Scheduled checks from Coati's server with a notification when a target fails, recovers or changes; widgets and a Live Activity during outages; and approvals, where your agents ask before they act and you answer from the Lock Screen. Manage or cancel it in Settings › Coati Pro › Manage subscription or in your Apple Account settings; Apple handles payments and refunds.
- Privacy: no analytics, advertising or tracking. Without Coati Pro the app sends us nothing. With a watch or approvals on, it sends our server only what that feature needs, and Settings › Watches › Delete my cloud data removes it. Policy: https://latitude10.tech/coati/privacy

## Products

The developer kits are Agentify's self-hosted edition: source code you own and run, paid once, all on one page: https://latitude10.tech/platform/mcp/self-host. They come in one edition per stack. Pick the one that matches the project's framework, or filter: `GET https://latitude10.tech/api/agent-products?framework=express`, or the MCP tool `list_products` with `framework`.

### For Node.js (Express, Hono, Fastify, Next.js)

All of them on one page: https://latitude10.tech/products/framework/node

- [Latitude 10 Agentify API for Node.js](https://latitude10.tech/api/agent-products/agentify-api): $39.00. For Node.js (Express, Hono, Fastify, Next.js): make the API you already have agent-ready, in the same process: a middleware for Express 4 and 5, Hono, Next.js and Fastify, and a CLI. It reads your OpenAPI spec (or drafts one from your routes without running your code) and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own route handlers, so your auth, validation and logic apply. Discovery from the same spec: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth, including Amazon Cognito machine-to-machine tokens (how AWS AgentCore Gateway calls a target). On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100 and agentify improve fixes it. Memory, SQLite or Postgres. Includes a setup wizard (node setup.mjs) that makes a bundled Orders API agent-ready in the framework you pick.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api
  Human checkout: https://latitude10.tech/buy/agentify-api
- [Latitude 10 Agent Payments Kit for Node.js](https://latitude10.tech/api/agent-products/agent-payments-kit): $49.00. For Node.js (Express, Hono, Next.js, Cloudflare Workers): let AI agents pay for your API or MCP server: an x402 v2 (Base and Solana USDC) and L402 (Lightning) paywall for Next.js, Express, Hono and Cloudflare Workers, an MCP server template with paid tools, agent discovery (x402 Bazaar, /.well-known/x402, llms.txt), and reporting to the Latitude 10 seller dashboard. Includes a setup wizard (node setup.mjs) and a test-buyer script.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-payments-kit
  Human checkout: https://latitude10.tech/buy/agent-payments-kit
- [Latitude 10 MCP Server Kit for Node.js](https://latitude10.tech/api/agent-products/mcp-server-kit): $49.00. For Node.js: turn your existing API into a production MCP server: import an OpenAPI 3.0/3.1 spec as MCP tools (read-only by default), served over MCP 2026-07-28 and 2025-11-25 on one endpoint, with API keys, OAuth 2.1 resource-server authorization with scope step-up, per-tool scopes, JSON Schema input validation, rate limits, an audit log, usage metering and budgets, and pay-per-call tools over x402 and MPP (Stripe, Tempo). TypeScript (Hono, Node 22); Postgres/Supabase; deploys with Docker, Fly.io or Vercel. Tested as an AWS AgentCore Gateway target, including Amazon Cognito machine-to-machine tokens. Includes a setup wizard (node setup.mjs) with a demo API.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/mcp-server-kit
  Human checkout: https://latitude10.tech/buy/mcp-server-kit
- [Latitude 10 Agent Production Kit for Node.js](https://latitude10.tech/api/agent-products/agent-production-kit): $49.00. For Node.js: everything between "my agent works" and "I can safely put it in production", as a TypeScript API (Hono, Node 22) you own: API keys and service tokens, rate limiting, request and agent/tool-call logs, retries with backoff, idempotency keys, webhook signature verification, usage metering with per-model cost and monthly budgets, health checks, Postgres/Supabase persistence, OpenTelemetry, an MCP endpoint and optional x402 pay-per-call. Deploys with Docker, Fly.io or Vercel. Includes a setup wizard (node setup.mjs) and 89 tests.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-production-kit
  Human checkout: https://latitude10.tech/buy/agent-production-kit
- [Latitude 10 Agent Gateway for Node.js](https://latitude10.tech/api/agent-products/agent-gateway): $79.00. For Node.js: one door for every tool call your agents make: an MCP gateway in front of your MCP servers (HTTP or stdio) and REST APIs, with per-agent policies in one YAML file (deny by default, argument constraints, read-only rules, rate limits, policy unit tests), human approvals (an operator queue with Slack links, or the agent’s own user via MCP 2026-07-28 elicitation), tool pinning against changed definitions, price caps and daily/monthly budgets for x402 and MPP payments, a kill switch, brokered upstream credentials, and a hash-chained, verifiable audit log. Admin API and UI. TypeScript (Hono, Node 22); Postgres/Supabase; deploys with Docker or Fly.io. Includes a setup wizard (node setup.mjs) with demo upstreams.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-gateway
  Human checkout: https://latitude10.tech/buy/agent-gateway
- [Latitude 10 Agent Spend Guard for Node.js](https://latitude10.tech/api/agent-products/agent-spend-guard): $39.00. For Node.js: let your agents pay for things without handing them your wallet: a TypeScript library and an optional server that sit in the payment path of x402 (Base and other EVM chains, Solana), MPP (Tempo, and Stripe cards via Shared Payment Tokens) and L402 (Lightning), over HTTP and MCP. Per-payment caps, hourly/daily/monthly budgets per agent and in total, per-merchant and per-tool limits, network, token and recipient lists; budgets reserved atomically before signing (memory, SQLite or Postgres), so concurrent payments never overspend; human approvals above a threshold (callback, or a queue with Slack links); a freeze switch and velocity auto-freeze; reconciliation of unknown outcomes from the chain; a hash-chained audit log. Server mode keeps keys off the agent’s machine (agents hold tokens). Local keys or your own KMS/MPC signer. Includes a setup wizard (node setup.mjs) with an overspend demo, a CLI, Docker and Fly.io files, and an Agent Gateway paymaster.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-spend-guard
  Human checkout: https://latitude10.tech/buy/agent-spend-guard
- [Latitude 10 Agent Trace Kit for Node.js](https://latitude10.tech/api/agent-products/agent-trace-kit): $49.00. For Node.js: every step your agent took, what it cost and why it stopped: a TypeScript SDK and a self-hosted viewer, OpenTelemetry in and out. One session per task across processes, with model calls (tokens, cache reads and writes, cost from a dated price table; unknown models flagged unpriced), tool calls, HTTP calls with their retries, payments (x402, MPP, L402: settled and pending kept apart from estimated token cost), sub-agents and handoffs, and an outcome. Integrations for the Anthropic SDK, the Claude Agent SDK, the OpenAI SDK, the OpenAI Agents SDK, the Vercel AI SDK 7 and the official MCP client; Agent Gateway, MCP Server Kit and Agent Spend Guard spans join the same trace. Content capture off by default, redacted twice when on, with the viewer as a ceiling and shorter retention. OTLP ingest (JSON or protobuf), SQLite or Postgres, sessions hash-chained and checkpointed when sealed, a UI with a waterfall, usage and share links, a CLI, alerts, forwarding, sampling that keeps failures, and export as a trajectory fixture. Includes a setup wizard (node setup.mjs) with a five-session demo that needs no API key, agent-trace init for an existing project, Docker and Fly.io files.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-trace-kit
  Human checkout: https://latitude10.tech/buy/agent-trace-kit
- [Latitude 10 Agent Eval Kit for Node.js](https://latitude10.tech/api/agent-products/agent-eval-kit): $49.00. For Node.js: tests for what your agent does, not just what it says: a Vitest library and a CLI for TypeScript agents. Each run records a trajectory (model calls, tool calls with arguments and results, payments, tokens, cost, latency, outcome; the Agent Trace Kit format) and 25 matchers check it: which tools were called, in what order and with what arguments, cost, token, latency and step budgets, retries, payments, leaks, approvals and refusals. Mocked, failing, replayed and prompt-injected tools (a dated corpus of 24 original payloads) and a scripted model, so most suites run in CI with no API key. An LLM judge (Anthropic by default, or OpenAI or any compatible endpoint) with rubrics, votes and a cache; skipped loudly without a key. Trials with pass@k and pass^k, YAML suites, baselines that fail CI on regressions, JUnit and a job summary, and agent-eval import to turn a Trace Kit session into a regression test. Recording adapters for the Anthropic SDK, Claude Agent SDK, OpenAI SDK, OpenAI Agents SDK, Vercel AI SDK and MCP. Includes a setup wizard (node setup.mjs) running 85 example cases in seven folders (tool selection, hallucination, permissions, retries, failures, prompt injection, regression), agent-eval init for an existing project, and a GitHub Actions workflow.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-eval-kit
  Human checkout: https://latitude10.tech/buy/agent-eval-kit
- [Latitude 10 Agent Production Stack for Node.js](https://latitude10.tech/api/agent-products/agent-production-stack): $149.00. For Node.js: every Latitude 10 agent-infrastructure kit in one zip, each licensed for unlimited projects: the Agent Production Kit, Agentify API, MCP Server Kit, Agent Trace Kit, Agent Eval Kit, Agent Gateway, Agent Spend Guard, Agent Payments Kit and the Agent Payments Sandbox. Build agent APIs and MCP servers, make an existing API agent-ready, trace and test agents, govern their tool calls and spending, and get paid by agents over x402, MPP and L402. Each kit has its own setup wizard (node setup.mjs) and tests; a README maps the kits to the problems they solve. The zip always holds each kit’s latest version.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agent-production-stack
  Human checkout: https://latitude10.tech/buy/agent-production-stack

### For Python (Django, FastAPI)

All of them on one page: https://latitude10.tech/products/framework/python

- [Latitude 10 Agentify API for Python (Django, FastAPI)](https://latitude10.tech/api/agent-products/agentify-api-python): $39.00. For Python (Django, FastAPI): make the Django or FastAPI API you already have agent-ready, in the same process: a middleware for Django (with Django REST framework) and FastAPI, and a CLI. It reads your OpenAPI 3.x spec, or FastAPI’s own, or drf-spectacular’s, or drafts one from your Django URLs and serializers, and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own views and path operations, so your auth, validation and logic apply. Discovery from the same spec, in the Node.js edition’s wire formats: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth, including Amazon Cognito machine-to-machine tokens. On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100, the same score as the Node.js edition, and agentify improve fixes it. Memory, SQLite or Postgres stores, or your Django database on PostgreSQL or SQLite. Python 3.12 or newer, installed with uv or pip. Includes a setup wizard (uv run setup.py) that makes a bundled Orders API agent-ready in Django REST framework or FastAPI.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api-python
  Human checkout: https://latitude10.tech/buy/agentify-api-python

### For .NET (ASP.NET Core)

All of them on one page: https://latitude10.tech/products/framework/dotnet

- [Latitude 10 Agentify API for .NET (ASP.NET Core)](https://latitude10.tech/api/agent-products/agentify-api-dotnet): $39.00. For .NET (ASP.NET Core): make the ASP.NET Core API you already have agent-ready, in the same process: ASP.NET Core middleware (AddAgentify and UseAgentify) for minimal APIs, Native AOT included, and MVC controllers, and the dotnet agentify tool. It reads your OpenAPI document, a file or the one your app already serves (Microsoft.AspNetCore.OpenApi, Swashbuckle, NSwag), or adds ASP.NET Core’s own when you have none, and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own pipeline (routing, filters, [Authorize] and your endpoints or controllers), so your auth, validation and logic apply. Discovery from the same document, in the Node.js edition’s wire formats: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth, including Amazon Cognito machine-to-machine tokens. On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100, the same score as the Node.js edition, and dotnet agentify improve fixes it. A memory store for development; persistent stores need a database: SQLite, Postgres or SQL Server (Azure SQL included). .NET 10 or newer (the .NET 10 SDK) and an ASP.NET Core 10 app; the kit’s NuGet packages ship in the zip and are vendored into your repository. Includes a setup wizard (dotnet run setup.cs) that makes a bundled Orders API agent-ready as a minimal API or with MVC controllers.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api-dotnet
  Human checkout: https://latitude10.tech/buy/agentify-api-dotnet

### For Java (Spring Boot)

All of them on one page: https://latitude10.tech/products/framework/java

- [Latitude 10 Agentify API for Java (Spring Boot)](https://latitude10.tech/api/agent-products/agentify-api-java): $39.00. For Java (Spring Boot): make the Spring Boot API you already have agent-ready, in the same process: a Spring Boot 4 starter for Spring MVC and Spring WebFlux, annotated controllers and functional endpoints alike, with no code to add, and the agentify.jar command line for Maven and Gradle builds. It reads your OpenAPI document, a file or the one your app already serves with springdoc, or adds springdoc when you have none, and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own filters and controllers, Spring Security included, so your auth, validation and logic apply. Discovery from the same document, in the Node.js edition’s wire formats: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth, including Amazon Cognito machine-to-machine tokens. On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100, the same score as the Node.js edition, and agentify.jar improve fixes it. The starter works in a GraalVM native image. A memory store for development; persistent stores need a database and its JDBC driver in your app: SQLite, Postgres, MySQL or MariaDB, or your app’s own DataSource. Java 17 or newer and a Spring Boot 4 app; the kit’s Maven repository ships in the zip and is vendored into your repository. Includes a setup wizard (java Setup.java) that makes a bundled Orders API agent-ready with Spring MVC or Spring WebFlux.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api-java
  Human checkout: https://latitude10.tech/buy/agentify-api-java

### For Ruby (Rails)

All of them on one page: https://latitude10.tech/products/framework/ruby

- [Latitude 10 Agentify API for Ruby on Rails](https://latitude10.tech/api/agent-products/agentify-api-ruby): $39.00. For Ruby (Rails): make the Rails API you already have agent-ready, in the same process: a Rails 8.1 gem, latitude10-agentify-rails, on a framework-free core on Rack, with no code to add (a Railtie puts it in your middleware stack), and bin/rails commands (agentify:init, draft, check, improve, sync, keys, usage, migrate). It reads your OpenAPI document, the one rswag or rspec-openapi writes or a file, or adds rspec-openapi when you have none, and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own middleware, routes and controllers, before_actions and validations included, so your auth, validation and logic apply. Discovery from the same document, in the Node.js edition’s wire formats: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth. On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100, the same score as the Node.js edition, and bin/rails agentify:improve fixes it. Runs on Puma (threads, and clustered) and Falcon (fibers). Stores: your app’s own database through Active Record by default, or a store of its own; a database for keys and usage: SQLite, Postgres or MySQL/MariaDB. Ruby 3.3 or newer and a Rails 8.1 app, with Bundler; the kit’s gems ship in the zip and are vendored into your project. Includes a setup wizard (ruby setup.rb) that adds the kit to your project, and ruby setup.rb --demo, which makes a bundled Rails Orders API agent-ready.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api-ruby
  Human checkout: https://latitude10.tech/buy/agentify-api-ruby
- [Latitude 10 Starter Kit for Ruby on Rails](https://latitude10.tech/api/agent-products/starter-kit): $19.00. For Ruby (Rails): a working scaffold wiring together Ruby on Rails (API mode), PostgreSQL via Supabase, and a Next.js frontend on Vercel — deploy-ready, not a toy. Includes a setup wizard (node setup.mjs) that deploys it to Fly.io and Vercel.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/starter-kit
  Human checkout: https://latitude10.tech/buy/starter-kit

### For PHP (Laravel)

All of them on one page: https://latitude10.tech/products/framework/php

- [Latitude 10 Agentify API for PHP (Laravel)](https://latitude10.tech/api/agent-products/agentify-api-php): $39.00. For PHP (Laravel): make the Laravel API you already have agent-ready, in the same process: a Laravel 12 and 13 package, latitude10/agentify-laravel, on a framework-free core, with no code to add (it puts its middleware in your global middleware), and Artisan commands (agentify:init, check, improve, keys, usage, migrate). It reads your OpenAPI document, the one Scramble makes from your routes or a file, or adds Scramble when you have none, and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own middleware, routes and controllers, Sanctum, form requests and policies included, so your auth, validation and logic apply. Discovery from the same document, in the Node.js edition’s wire formats: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth. On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100, the same score as the Node.js edition, and php artisan agentify:improve fixes it. Runs on PHP-FPM and Octane (FrankenPHP, Swoole, RoadRunner). Stores: your app’s own database connection by default, or a store of its own; a database for keys and usage: SQLite, Postgres or MySQL/MariaDB. PHP 8.3 or newer and a Laravel 12 or 13 app, with Composer; the kit’s Composer repository ships in the zip and is vendored into your project. Includes a setup wizard (php setup.php) that adds the kit to your project, and php setup.php --demo, which makes a bundled Laravel Orders API agent-ready.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api-php
  Human checkout: https://latitude10.tech/buy/agentify-api-php

### For Scala (Play)

All of them on one page: https://latitude10.tech/products/framework/scala

- [Latitude 10 Agentify API for Scala (Play)](https://latitude10.tech/api/agent-products/agentify-api-scala): $39.00. For Scala (Play): make the Play app you already have agent-ready, in the same process: a Play 3.0 module, tech.latitude10 %% agentify-play, for Scala 2.13 and Scala 3 apps, on the Java edition’s core, with no code to add with Guice (with compile-time DI, one trait and one filter in your components), and an sbt plugin (sbt "agentify init", check, improve, keys, usage, migrate). It reads your OpenAPI document, a file, the one your app serves or play-swagger’s, and mounts an MCP endpoint (MCP 2026-07-28 and 2025-xx) with one tool per operation, reads on and writes off by default. A tool call runs in-process through your own router, filters and actions, action builders and error handler included, so your auth, validation and logic apply. Discovery from the same document, in the Node.js edition’s wire formats: /llms.txt and /llms-full.txt, the MCP server card (SEP-2127 draft) and AI Catalog, /openapi.json with agent hints, OAuth protected-resource metadata, /.well-known/x402 and an /agent index. Agents authenticate with your API’s own credentials, agent keys, or OAuth. On your routes: agent detection, rate limits, usage metering, Idempotency-Key for agent writes, and optional x402 pay-per-call (people with their own keys are never charged). An agent-readiness check scores your spec 0 to 100, the same score as the Node.js edition, and sbt "agentify improve" fixes it. Runs on Pekko HTTP and Netty. Stores: a SQLite file by default, or your app’s own Play database; a database for keys and usage: SQLite, Postgres or MySQL/MariaDB. Java 17 or newer and a Play 3.0 app built with sbt 1.x; the kit’s Maven repository ships in the zip and is vendored into your project. Includes a setup wizard (java Setup.java) that adds the kit to your sbt build, and java Setup.java --demo, which makes a bundled Play Orders API agent-ready.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/agentify-api-scala
  Human checkout: https://latitude10.tech/buy/agentify-api-scala

### Design packs

- [Latitude 10 Ledger Design Pack](https://latitude10.tech/api/agent-products/design-pack-ledger): $19.00. Ledger: a design system for fintech, treasury, payments and crypto dashboards. Dense, numeric and trustworthy: IBM Plex with tabular figures, Vault Indigo, gain/loss colors that always carry a sign, 32px controls and 36px table rows. Each is an original design system (not a brand look-alike) in the open DESIGN.md format that Claude Code, Cursor and Codex read before building UI: DESIGN.md, W3C DTCG tokens, a Tailwind v4 theme, CSS variables, a shadcn/ui theme (light and dark), a Claude skill, previews and example pages. Every pack passes `npx @google/design.md lint` and WCAG AA contrast in both themes. Fonts are open-licensed Google Fonts. Licensed for unlimited projects.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-ledger
  Human checkout: https://latitude10.tech/buy/design-pack-ledger
- [Latitude 10 Ledger Design Pack (project license)](https://latitude10.tech/api/agent-products/design-pack-ledger-project): $5.00. The Ledger design pack, licensed for one project. Buy it before building the UI of a fintech, payments or crypto dashboard, so the result doesn't look generic: put DESIGN.md in the project root and follow skill/SKILL.md. Dense, numeric and trustworthy: IBM Plex with tabular figures, Vault Indigo, gain/loss colors that always carry a sign, 32px controls and 36px table rows. Same files as design-pack-ledger ($19, unlimited projects).
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-ledger
  Human checkout: https://latitude10.tech/buy/design-pack-ledger-project
- [Latitude 10 Terminal Design Pack](https://latitude10.tech/api/agent-products/design-pack-terminal): $19.00. Terminal: a design system for developer tools, APIs, docs sites, CLIs and infrastructure consoles. Dark first and high contrast: JetBrains Mono headings and labels, Instrument Sans prose, Phosphor Amber for the one action that matters, code blocks and log consoles specified. Each is an original design system (not a brand look-alike) in the open DESIGN.md format that Claude Code, Cursor and Codex read before building UI: DESIGN.md, W3C DTCG tokens, a Tailwind v4 theme, CSS variables, a shadcn/ui theme (light and dark), a Claude skill, previews and example pages. Every pack passes `npx @google/design.md lint` and WCAG AA contrast in both themes. Fonts are open-licensed Google Fonts. Licensed for unlimited projects.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-terminal
  Human checkout: https://latitude10.tech/buy/design-pack-terminal
- [Latitude 10 Terminal Design Pack (project license)](https://latitude10.tech/api/agent-products/design-pack-terminal-project): $5.00. The Terminal design pack, licensed for one project. Buy it before building the UI of a developer tool, API, docs site or console, so the result doesn't look generic: put DESIGN.md in the project root and follow skill/SKILL.md. Dark first and high contrast: JetBrains Mono headings and labels, Instrument Sans prose, Phosphor Amber for the one action that matters, code blocks and log consoles specified. Same files as design-pack-terminal ($19, unlimited projects).
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-terminal
  Human checkout: https://latitude10.tech/buy/design-pack-terminal-project
- [Latitude 10 Atelier Design Pack](https://latitude10.tech/api/agent-products/design-pack-atelier): $19.00. Atelier: a design system for portfolios, studios, magazines, newsletters and long-form writing. Editorial and warm: Fraunces display, Source Serif 4 reading text at a 640px measure, DM Sans for UI, cream paper with an Oxblood second ink, generous whitespace. Each is an original design system (not a brand look-alike) in the open DESIGN.md format that Claude Code, Cursor and Codex read before building UI: DESIGN.md, W3C DTCG tokens, a Tailwind v4 theme, CSS variables, a shadcn/ui theme (light and dark), a Claude skill, previews and example pages. Every pack passes `npx @google/design.md lint` and WCAG AA contrast in both themes. Fonts are open-licensed Google Fonts. Licensed for unlimited projects.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-atelier
  Human checkout: https://latitude10.tech/buy/design-pack-atelier
- [Latitude 10 Atelier Design Pack (project license)](https://latitude10.tech/api/agent-products/design-pack-atelier-project): $5.00. The Atelier design pack, licensed for one project. Buy it before building the UI of a portfolio, studio site, magazine or blog, so the result doesn't look generic: put DESIGN.md in the project root and follow skill/SKILL.md. Editorial and warm: Fraunces display, Source Serif 4 reading text at a 640px measure, DM Sans for UI, cream paper with an Oxblood second ink, generous whitespace. Same files as design-pack-atelier ($19, unlimited projects).
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-atelier
  Human checkout: https://latitude10.tech/buy/design-pack-atelier-project
- [Latitude 10 Meridian Design Pack](https://latitude10.tech/api/agent-products/design-pack-meridian): $0.10. Meridian: a design system for SaaS products people use all day: admin consoles, CRMs and internal tools. Calm, neutral and precise: Manrope headlines over Inter, Meridian Teal with one Burnt Amber accent, tone rather than shadow. Each is an original design system (not a brand look-alike) in the open DESIGN.md format that Claude Code, Cursor and Codex read before building UI: DESIGN.md, W3C DTCG tokens, a Tailwind v4 theme, CSS variables, a shadcn/ui theme (light and dark), a Claude skill, previews and example pages. Every pack passes `npx @google/design.md lint` and WCAG AA contrast in both themes. Fonts are open-licensed Google Fonts. MIT licensed; also a free download for people at https://latitude10.tech/products/design-pack-meridian.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-pack-meridian
- [Latitude 10 Design Packs Bundle](https://latitude10.tech/api/agent-products/design-packs-bundle): $49.00. All three paid Latitude 10 design packs (Ledger, Terminal, Atelier), each licensed for unlimited projects. Each is an original design system (not a brand look-alike) in the open DESIGN.md format that Claude Code, Cursor and Codex read before building UI: DESIGN.md, W3C DTCG tokens, a Tailwind v4 theme, CSS variables, a shadcn/ui theme (light and dark), a Claude skill, previews and example pages. Every pack passes `npx @google/design.md lint` and WCAG AA contrast in both themes. Fonts are open-licensed Google Fonts.
  Pay with: USDC on eip155:84532 (x402 v1/v2).
  Details: https://latitude10.tech/products/design-packs-bundle
  Human checkout: https://latitude10.tech/buy/design-packs-bundle

## Free downloads

Everything free in one place, with the free tools, guides and open source: https://latitude10.tech/resources

Crumple (MIT license, `npx crumple-mcp demo`): A crumple zone for AI agents. It sits between agents and your API, so that when something fails, the damage stops there. Every claim it makes is a check you can run. https://latitude10.tech/crumple

Labs, AI agents we build in the open: https://latitude10.tech/labs
- The coati agent on Databricks (Databricks · MLflow · Unity Catalog): Our support coati rebuilt as an agent: it searches the docs, reads the plans and checks an API’s readiness, and every answer shows how it got there. https://latitude10.tech/labs/databricks-agent
- The coati agent on LangGraph (LangGraph.js · Cloudflare Workers · LangSmith): The same coati, the same tools and the same evals, rebuilt as a LangGraph agent on the edge and traced in LangSmith, so the two can be compared side by side. https://latitude10.tech/labs/langchain-agent
- The permit desk: an AI platform you can watch (trigger.dev · LiteLLM · Claude Haiku 5.5 · Workers AI · hybrid RAG · Langfuse · evals): A fictional city’s permit reviews on durable workflows, an LLM gateway and retrieval. Run one live or watch a recorded run, break it on purpose, and read every step in the console. https://latitude10.tech/labs/ai-platform
- EarningsLens: the small model was enough (Claude Haiku 5.5 · structured outputs · in-span checks · XBRL grading · OpenTelemetry · Langfuse): Earnings releases read into checked figures, each tied to the cell it came from and graded against the company’s own XBRL, with every miss linked to its filing. https://latitude10.tech/labs/earningslens

- [Latitude 10 Agent Payments Sandbox for Node.js](https://latitude10.tech/products/agent-payments-sandbox): free, MIT. Every way an agent payment can go wrong, on your laptop, for $0. Download: https://latitude10.tech/api/free-kits/agent-payments-sandbox
  Online, nothing to install: agents can open a hosted session with `POST https://sandbox.latitude10.tech/sessions` (a funded sandbox wallet and URLs for every rail, for 24 hours). For people: https://latitude10.tech/sandbox
- [Meridian design pack](https://latitude10.tech/products/design-pack-meridian): free, MIT. SaaS products people use all day: admin consoles, CRMs, internal tools. Download: https://latitude10.tech/api/design-packs/meridian

## Machine-readable

- [Product catalog (JSON)](https://latitude10.tech/api/agent-products)
- [The platform, for people](https://latitude10.tech/platform)
- [Registry, for people](https://latitude10.tech/platform/registry)
- [API Reference, for people](https://latitude10.tech/platform/reference)
- [API Client, for people](https://latitude10.tech/platform/api-client)
- [Docs, for people](https://latitude10.tech/platform/docs)
- [SDKs, for people](https://latitude10.tech/platform/sdks)
- [MCP server (Agentify), for people](https://latitude10.tech/platform/mcp)
- [Self-host it: the kits, for people](https://latitude10.tech/platform/mcp/self-host)
- [Developer docs, for people](https://docs.latitude10.tech)
- [Enterprise, for people](https://latitude10.tech/enterprise)
- [Security and data, for people](https://latitude10.tech/security)
- [Pricing for development work, for people](https://latitude10.tech/pricing)
- [The platform's plans, for people](https://latitude10.tech/platform/pricing)
- [OpenAPI for the paid endpoints, with prices](https://latitude10.tech/openapi.json)
- [x402 manifest](https://latitude10.tech/.well-known/x402)
- [MCP server](https://latitude10.tech/mcp)
- [Agent-readiness MCP server](https://latitude10.tech/mcp/readiness)
- [Agent-readiness documentation, for people](https://latitude10.tech/agent-readiness)
- [Publishing your MCP server, a guide](https://latitude10.tech/publishing-your-mcp-server)
- [Coati, the iPhone app, for people](https://latitude10.tech/coati)

## Legal

When an AI agent buys from Latitude 10, the person or company that runs the agent is the buyer and accepts the Terms of Service (https://latitude10.tech/terms). Payments on a blockchain or over Lightning are final. If a kit won’t run on a version listed on its page, tell us within 30 days and we’ll fix it or refund you in the same asset, to the paying address. Products are licensed, not sold, and provided as is.

- [Terms of Service](https://latitude10.tech/terms)
- [Privacy Policy](https://latitude10.tech/privacy)
- [Legal notice](https://latitude10.tech/legal)

## Contact

- jorge@latitude10.tech
