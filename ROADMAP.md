# In next release 

1. Barcode Scanning with camera
2. French Language support 

# User management

This is long overdue, uBiblio is multi-user but has no user management, making it very hard to use for book clubs and so on.

1. Admins should be able to create a temporary link that lets a new user create a login. For example, they send the link to their friend, and their friend creates an account.
2. Login links should expire in 24 hrs if unused
3. There should be a 'root' account level. The owner should be able to set / unset admin rights on user accounts.
4. Admin and Root are booleans.
5. Still not going to add password recovery. However, might be nice to be able to change my password.

# Federation

The goal here is twofold -- first, to allow something like the pre-search-engine inter-library search features of the early 1990s. Second, to make it easier for groups of people, who are perfectly happy running their own libraries, to have better options than merging their databases (although merges are already supported).

1. Instances of uBiblio should generate a public-private keypair on first launch, and store it in the DB.
2. The public key will be exposed on an endpoint that requires no login, e.g. /key
3. If an admin points a ubiblio instance to another (e.g. submits the URL), it will grab the key and store it.
4. Users should be able to submit book searches to these other instances. This will be an endpoint on their local instance, which will sign the request and pass it to the target.
5. If uBiblio receives a search request signed by a key that has been authorized, it will serve the search request without requiring a login.
6. Maybe offer some expedited way to get a user account -- e.g. request one, and admins get notified on login.
7. It should also be possible to manually add a public key (e.g. to let libraries without a public IP run federated searches)

# Quality of Life
1. I think I can let people search book databases by title + author, and selecto ne to add. This will help with libraries of very old, pre-ISBN books.
2. I think I could add a warning when you are adding something that is very probably a duplicate book.
3. I need to eventually add a more scalable localization strategy. For just French a new set of templates is fine, but for more languages it will need to be something smarter.
