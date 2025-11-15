This is a file where I list out things I plan to add to uBiblio. You can suggest new things by raising an issue!

# In next release 

1. Barcode Scanning with camera
2. French Language support 
3. User creation and management
4. Some UI fixes
5. Use local files for barcode scanner and JQuery instead of constantly downloading them

# User management
1. Should there be a 'root' account level? The root account cannot be deleted, and can delete/promote/demote admin accounts.
2. Still not going to add password recovery. However, might be nice to be able to change my password.

# Privacy
1. Should use local fonts instead of downloading them from google fonts.

# Federation

The goal here is twofold -- first, to allow something like the pre-search-engine inter-library search features of the early 1990s. Second, to make it easier for groups of people, who are perfectly happy running their own libraries, to have better options than merging their databases (although merges are already supported).

1. Instances of uBiblio should generate a public-private keypair on first launch, and store it in the DB or in a file.
2. The public key will be exposed on an endpoint that requires no login, e.g. /key
3. If an admin points a ubiblio instance to another (e.g. submits the URL), it will grab the key and store it.
4. Users should be able to submit book searches to these other instances. This will be an endpoint on their local instance, which will sign the request and pass it to the target.
5. If uBiblio receives a search request signed by a key that has been authorized, it will serve the search request without requiring a login.
6. Maybe offer some expedited way to get a user account -- e.g. request one, and admins get notified on login.
7. It should also be possible to manually add a public key (e.g. to let libraries without a public IP run federated searches)

# Quality of Life
1. I think I can let people search book databases by title + author, and select one to add. This will help with libraries of very old, pre-ISBN books.
2. I think I could add a warning when you are adding something that is very probably a duplicate book.
3. I need to eventually add a more scalable localization strategy. For just French a new set of templates is fine, but for more languages it will need to be something smarter.
4. Books should have a 'date added' field.
