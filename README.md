# Features:

It's ubiblio -- but smaller. If we're being SI-compliant, it should be called nbiblio. It's also cursed.

# ...Smaller?

ubiblio takes up around 90MB of memory and is pretty snappy, even though python doesn't usually have the best reputation for speed. 

So since it's already taking under 100MB of memory, why host it on a huge server box? Even an old laptop is way too powerful. An old phone? Still way too huge and wasteful. A raspberry pi would work fine, but what will I even do with all that extra memory?

No, it must run on a system the size of a postage stamp. 

# ...Cursed?

So I noticed that a local vendor was stocking a perfectly cromulent little RISCV board, the LicheeRV Nano. The CPU is from Sophgo, a manufacturer I had never heard of. A quick search revealed three things, and then another thing:

1. It looks like I can cross-compile Debian for it!
2. It also looks like the company is being accused of something or other, and will probably be banned in the USA.
3. The architechture is RISCV64, and it has an unctuously luxurious 256 MB of memory. Also integrated Wi-Fi and a little slot for an SD card.
4. Support for this thing is limited. Mysteries abound!

# Cross-compiling Debian

The heavy lifting was done here: https://github.com/Fishwaldo/sophgo-sg200x-debian

I did manage to eventually get Debian to cross-compile, however I ham-fistedly forgot to include any useful packages. So finally I just used the pre-compiled image generously provided by the author of that repository, and just added things as needed. It turns out Debian on riscv64 is quite OK!

# Setting up nbiblio

The current install process almost just works, surprisingly. We can forget about Docker images, we don't really have the memory to spare. So we should use venv and no containers.

The main issue is that Python 3.12 is incompatible with ubiblio, because of an issue with Pydantic. So we must make sure not to install Python 3.12. I tried upgrading everything to 3.12, but there are too many issues to fix while compiling newer Pydantic versions (OOM, out of storage, etc.)
