# sketch.py — Dynamic FUSE directory design sketch

## Problem

`chatfs-fuser`'s `dir_each` evaluates `list_fn` at build time. The directory
tree is frozen at `.build()`. New conversations don't appear until remount.

## Key insight

FUSE's `read(ino)` only receives an inode — but `lookup(parent, name)` always
runs first. The library can lazily record inode-to-path mappings in `lookup`,
then resolve paths back to user callbacks in `read`. No eager expansion needed,
no mutable node map — just a growing translation table.

Three layers in the sketch:
1. **FuseRequest** — simulates the kernel's inode-only interface
2. **VFS** — the library's inode ↔ path translation layer (the new thing)
3. **UserVFSModule** — user's business logic, wired into framework types

## Open design question

`construct_vfs()` requires the user to wrap business logic in framework types
(`DynamicDir`, `File`) with closures for partial application. The remaining
lambdas exist because `template(name) -> Entry` must close over the parent
segment name to parameterize child callbacks.

Can the framework handle this parameter threading so the user doesn't write
closures? This resembles URL routing, where parent path segments determine
child handler semantics.

## Prior art: URL routing frameworks

**FastAPI** — dependency injection via `Depends()` chains.
`resolve_convo` declares `Depends(resolve_org)`, framework builds the DAG.
Handler receives resolved objects, never touches raw path segments.
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Sub-dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/sub-dependencies/)
- Source: [dependencies/index.md](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/dependencies/index.md), [sub-dependencies.md](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/dependencies/sub-dependencies.md)

**Axum** — `Router::nest()` + `FromRequestParts` extractors.
Same idea as FastAPI but type-driven. Custom extractors compose via the trait system.
- [Router::nest](https://docs.rs/axum/latest/axum/struct.Router.html#method.nest)
- [Path extractor](https://docs.rs/axum/latest/axum/extract/struct.Path.html)
- Source: [nest.md](https://github.com/tokio-rs/axum/blob/main/axum/src/docs/routing/nest.md), [extract.md](https://github.com/tokio-rs/axum/blob/main/axum/src/docs/extract.md)

**React Router** — tree-structured route config with per-node `loader`.
Child loaders receive all parent params. `useRouteLoaderData(id)` accesses
ancestor data. Structural nesting mirrors URL hierarchy.
- [Routing (Data Mode)](https://reactrouter.com/start/data/routing)
- [createBrowserRouter](https://api.reactrouter.com/v7/functions/react_router.createBrowserRouter.html)

**Express** — `Router({ mergeParams: true })` + `router.param()`.
`mergeParams` makes parent params visible in child routers.
`router.param('org_id', cb)` resolves once per request before handlers.
- [express.Router](https://expressjs.com/en/4x/api.html#express.router)
- [router.param](https://expressjs.com/en/4x/api.html#router.param)
- Source: [routing.md](https://github.com/expressjs/expressjs.com/blob/gh-pages/en/guide/routing.md), [api.md](https://github.com/expressjs/expressjs.com/blob/gh-pages/en/4x/api.md)

**Flask** — flat. All dynamic segments passed as kwargs. No semantic nesting.
Handler manually resolves parents. Least ergonomic for this pattern.
- [Nesting Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/#nesting-blueprints)
- Source: [blueprints.rst](https://github.com/pallets/flask/blob/main/docs/blueprints.rst)

## Running the sketch

```bash
python3 packages/chatfs-fuser/docs/design-incubators/dynamic-routing/demo.py
```
