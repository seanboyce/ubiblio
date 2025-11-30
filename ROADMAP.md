This is a file where I list out things I plan to add to uBiblio. You can suggest new things by raising an issue!

# In next release 

1. Barcode Scanning with camera
2. French Language support 
3. User creation and management
4. Some UI fixes
5. Use local files for barcode scanner and JQuery instead of constantly downloading them
6. Federated search and viewing book details

# User management
1. Should there be a 'root' account level? The root account cannot be deleted, and can delete/promote/demote admin accounts.
2. Still not going to add password recovery. However, might be nice to be able to change my password.

# Privacy
1. Should use local fonts instead of downloading them from google fonts.

# Federation

The goal here is twofold -- first, to allow something like the pre-search-engine inter-library search features of the early 1990s. Second, to make it easier for groups of people, who are perfectly happy running their own libraries, to have better options than merging their databases (although merges are already supported). This is a list of unimplemented features related to federation.

1. Maybe offer some expedited way to get a user account -- e.g. request one, and admins get notified on login and can just activate it.


# Quality of Life
1. I think I can let people search book databases by title + author, and select one to add. This will help with libraries of very old, pre-ISBN books.
2. I think I could add a warning when you are adding something that is very probably a duplicate book (but this might be hard).
3. I need to eventually add a more scalable localization strategy. For just French a new set of templates is fine, but for more languages it will need to be something smarter.
4. Books should have a 'date added' field.
5. I should add a library stats page. It will be basic, just count/sum and group_by on different fields, including custom fields.
6. There should be an 'about' page. By default, it includes some instructions for new users. However, it will also contain some sections designed to be filled out by users if they want, e.g. 'about this library', 'rules', or just 'how to apply for a user account'. This page requires login or federated access.
