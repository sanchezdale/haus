# Publish a Static Homeowner Manual to Cloudflare Pages, then Gate It with Cloudflare Access

Works from a Mac with a plain folder of HTML/CSS/JS, no build step, no server. Total time is roughly 15 minutes, and everything used here (Pages static hosting, Access on the Zero Trust Free plan) costs nothing for a single household.

## 1. One-time setup: Wrangler, Node, login

Wrangler is the Cloudflare CLI. It needs Node.js (any release in Current, Active, or Maintenance status) and npm, and runs on macOS 13.5 or newer ([Wrangler install guide](https://developers.cloudflare.com/workers/wrangler/install-and-update/)). If Wrangler is not installed, `npx wrangler` runs the latest release, which is all a one-off personal deploy needs ([same page](https://developers.cloudflare.com/workers/wrangler/install-and-update/)).

```sh
npx wrangler --version
npx wrangler login
```

`wrangler login` opens your browser for an OAuth authorization against your Cloudflare account ([login command reference](https://developers.cloudflare.com/workers/wrangler/commands/general/)). If the local callback flow is blocked, use `npx wrangler login --device` instead ([same reference](https://developers.cloudflare.com/workers/wrangler/commands/general/)). You can confirm the session with `npx wrangler whoami`.

## 2. Create the project and deploy the folder

Create the Pages project once (you will be served at `<PROJECT_NAME>.pages.dev`, or your project name plus a few random characters if the name is already taken) ([Direct Upload guide](https://developers.cloudflare.com/pages/get-started/direct-upload/)):

```sh
npx wrangler pages project create haus --production-branch=main
```

Deploy the folder of static files (positional name and flags per the [Pages command reference](https://developers.cloudflare.com/workers/wrangler/commands/pages/)):

```sh
npx wrangler pages deploy ./site --project-name=haus
```

Notes, all from the [Direct Upload guide](https://developers.cloudflare.com/pages/get-started/direct-upload/):

- If the project does not exist yet, `pages deploy` prompts you and creates it, so the two commands can collapse into one.
- Your production deployment is available at `https://haus.pages.dev`. Later updates are just this same command again.
- Wrangler Direct Upload takes a single folder of assets (no zip), with a limit of 20,000 files and 25 MiB per file.
- Git gotcha if your deploy folder lives inside a git repository: Wrangler automatically pulls branch information from git. If your current branch is not the production branch, your upload becomes a preview deployment at `<branch>.<project>.pages.dev`. Pass `--branch=main` explicitly (preview branch command, [same guide](https://developers.cloudflare.com/pages/get-started/direct-upload/)) or deploy from the production branch.

Git-integration alternative, one line: connecting a repository lets Pages build and deploy automatically on every push ([Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/)), but it requires the manual to live in a repo; Direct Upload pushes the folder straight from the Mac to Cloudflare, so nothing is ever exposed in a repository. Also note a Direct Upload project cannot be switched to Git later, you would create a new project ([Direct Upload guide](https://developers.cloudflare.com/pages/get-started/direct-upload/)).

## 3. Gate it with Cloudflare Access

Access is part of Zero Trust. If you have never opened it, enable Zero Trust once from the Cloudflare dashboard (guided setup, [Zero Trust get started](https://developers.cloudflare.com/cloudflare-one/setup/)). The Zero Trust Free plan covers up to 50 users, described as "teams under 50 users" with a "50 user limit" ([Cloudflare Access pricing](https://www.cloudflare.com/sase/products/access)); a seat is consumed when a user first authenticates, and once seats run out additional users are blocked ([seat management](https://developers.cloudflare.com/cloudflare-one/team-and-resources/users/seat-management/)).

### The Pages dashboard path (this is the documented route for a pages.dev hostname)

Does the Pages dashboard offer an alternative to creating an app in Zero Trust? Yes, and for a `pages.dev` hostname it is the path Cloudflare documents, because the standard Zero Trust "self-hosted" flow requires the hostname to be a domain in an active zone in your account, and `pages.dev` is a Cloudflare-managed hostname ([self-hosted application guide](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/)). Steps:

1. Cloudflare dashboard, **Workers & Pages**, select your Pages project, **Settings > General**, select **Enable access policy**. This creates an Access application and restricts preview deployments to your Cloudflare account, but it only protects preview URLs, not your production `*.pages.dev` domain or a custom domain ([preview deployments: Customize preview deployments access](https://developers.cloudflare.com/pages/configuration/preview-deployments/)).
2. To gate the production hostname: select **Manage** on the access policy that was created, then under **Access > Applications** select your project, **Configure**, and under **Public hostname** delete the wildcard in the **Subdomain** field and **Save** (rename the application if it throws an error). Your `<project>.pages.dev` domain is now behind Access ([Known issues: Enable Access on your pages.dev domain](https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain)).
3. Go back to the Pages project, **Settings > General**, and reselect **Enable access policy** so a second policy is recreated for previews (`*.<project>.pages.dev`), leaving you with two policies, one for the production domain and one for previews ([same Known issues section](https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain)).
4. Tune the allow policy: in **Zero Trust > Access controls > Applications**, open each of the two applications and check its policy. Use an **Allow** action with an **Include** rule: selector **Emails** with your address, or selector **Emails ending in** with `@yourdomain.com`. All Access applications are deny by default, a user must match an Allow policy ([policies reference](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/)). Do not use Include "Everyone" or Include all One-time PIN login methods; the policies doc lists both as misconfigurations that open the site to anyone ([common misconfigurations](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/)).

### Login method

New Zero Trust organizations use the Cloudflare identity provider as the default login method, so you can sign in with the Cloudflare account you already have. You can also add **One-time PIN** (Zero Trust, **Integrations > Identity providers > Add new identity provider > One-time PIN**) so any email your policy allows can receive a login code ([One-time PIN login](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/)). Allowed users enter their email on the Access login page, receive a code that expires after 10 minutes, and sign in ([same page](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/)).

### What unauthorized visitors see

Anyone not on the allow list hits the Access login page ([Access login page](https://developers.cloudflare.com/cloudflare-one/reusable-components/custom-pages/access-login-page/)) and never receives your site content. Cloudflare only emails a code to addresses allowed by a policy, and a user who submits without a valid code gets the default block message, "That account does not have access", displayed below the Cloudflare Access logo ([One-time PIN login](https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/) and [self-hosted application guide, custom block pages](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/)).

### If you later add a custom domain

The classic Zero Trust flow does apply to a custom domain (a hostname in a zone on your account): **Zero Trust > Access controls > Applications > Create new application > Self-hosted and private > Add public hostname**, then add your Allow policy ([self-hosted application guide](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/)). Caution: if you gate `pages.dev` and add a custom domain, you must create this separate Access application for the custom domain, otherwise the login screen renders but does not authenticate visitors on that hostname ([Known issues caution](https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain)).

## 4. Gotchas for a single-user personal deploy

- **Custom domain, optional:** skip it, `<project>.pages.dev` is fine. If you want one, select the project, **Custom domains**, **Set up a domain**; an apex domain needs its zone on Cloudflare, a subdomain can be a CNAME to `<project>.pages.dev` ([custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/)). Remember the Access caveat above.
- **Asset limits:** on the Free plan a Pages site can contain up to 20,000 files, each up to 25 MiB, with 100 custom domains and 100 projects per account ([Pages limits](https://developers.cloudflare.com/pages/platform/limits/)). A homeowner manual of HTML, CSS, and JS will not come close.
- **Project name permanence:** the `*.pages.dev` subdomain cannot be changed later; you would delete the project and create a new one, and Cloudflare rate limits new project creation during your first 48 hours ([Known issues](https://developers.cloudflare.com/pages/platform/known-issues/) and [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)).
- **No switching to Git later** on a Direct Upload project ([Direct Upload guide](https://developers.cloudflare.com/pages/get-started/direct-upload/)). Irrelevant unless you change your mind later; the workaround is a new project.
- **Offline and queue behavior, ignore it:** Direct Upload has no build queue (the "1 build at a time" and "500 builds per month" limits apply to Git integration builds only, [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)), and the site is served from the Cloudflare global network, so it stays online even when your Mac is asleep or off ([Pages overview](https://developers.cloudflare.com/pages/)). If an upload is interrupted, just rerun the deploy command, and you can roll back to any previous deployment from the dashboard ([rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/)).

Update routine from here: edit files on the Mac, then:

```sh
npx wrangler pages deploy ./site --project-name=haus
```

## Sources

- https://developers.cloudflare.com/pages/get-started/direct-upload/
- https://developers.cloudflare.com/pages/get-started/git-integration/
- https://developers.cloudflare.com/workers/wrangler/install-and-update/
- https://developers.cloudflare.com/workers/wrangler/commands/general/
- https://developers.cloudflare.com/workers/wrangler/commands/pages/
- https://developers.cloudflare.com/pages/platform/limits/
- https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain
- https://developers.cloudflare.com/pages/configuration/preview-deployments/
- https://developers.cloudflare.com/pages/configuration/custom-domains/
- https://developers.cloudflare.com/pages/configuration/rollbacks/
- https://developers.cloudflare.com/pages/
- https://developers.cloudflare.com/cloudflare-one/setup/
- https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/
- https://developers.cloudflare.com/cloudflare-one/access-controls/policies/
- https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/one-time-pin/
- https://developers.cloudflare.com/cloudflare-one/reusable-components/custom-pages/access-login-page/
- https://developers.cloudflare.com/cloudflare-one/team-and-resources/users/seat-management/
- https://www.cloudflare.com/sase/products/access
