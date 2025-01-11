
# What is this?

This is the port of ubiblio for riscv64. The code should remain the same, but in case it doesn't, I've created this branch.


The feature set is the same. It's physcically much smaller. I guess we can call it nbiblio instead of ubiblio, if you'll pardon my grecolatin.

# Why?


I have no idea. It just sort of happened. We all make mistakes sometimes.

# OK, but does it work?

Yes, it works *surprisingly* well. It's reasonably fast. Pages load for me in less than half a second -- if you try really hard you may notice it is very slightly slower than using a modern computer by some milliseconds. Memory usage sits around 55% -- a bit under 100MB for ubiblio, and some overhead for redis and uvicorn and so on.

I originally conceived this as some sort of joke for your amusement, but it accidentally worked (sorry).

# ...Smaller?

ubiblio takes up around 90MB of memory and is pretty snappy, even though python doesn't usually have the best reputation for speed. 

So since it's already taking under 100MB of memory, why host it on a huge server box? Even an old laptop is way too powerful. An old phone? Still way too huge and wasteful. A raspberry pi would work fine, but what will I even do with all that extra memory?

No, it must run on a system the size of a postage stamp. 

![Here is a photo](https://github.com/seanboyce/ubiblio/blob/cursed/nbiblio.JPG)

# ...How did this happen?

So I noticed that a local vendor was stocking a perfectly cromulent little RISCV board, the LicheeRV Nano. The CPU is from Sophgo, a manufacturer I had never heard of. A quick search revealed three things, and then another thing:

1. It looks like I can cross-compile Debian for it!
2. It also looks like the company is being accused of something or other, and will probably be banned in the USA.
3. The architechture is RISCV64, and it has an unctuously luxurious 256 MB of memory. Also integrated Wi-Fi and a little slot for an SD card.
4. Support for this thing is limited. Mysteries abound!

# Cross-compiling Debian

The heavy lifting was done here: https://github.com/Fishwaldo/sophgo-sg200x-debian

I did manage to eventually get Debian to cross-compile, however I ham-fistedly forgot to include any useful packages. So finally I just used the pre-compiled image generously provided by the author of that repository, and just added things as needed. It turns out Debian on riscv64 is quite OK!

As an aside, I ended up soldering in a serial port, and used that to login / install everything. However the board also does networking over USB and you can just connect to it over SSH.

# Setting up nbiblio

The normal install process almost just works, surprisingly. We can forget about Docker images though, we don't really have the memory to spare. So we should use venv and no containers.

Issues arise as follows:

1. ubiblio needs Python 3.10-3.12. There's a specific version of 3.12 that breaks it, because of a bug in Pydandic. That bug has since been fixed in Pydantic 2.X. So you need *either* Python 3.10 up to early 3.12 and Pydantic ~1.10.2... or Python 3.12 and Pydandic 2.X.
2. Only Python 3.12 is available for riscv64, So we need to upgrade to recent Pydantic. However, pip needs to compile it, and we hit out of memory (OOM) errors.
3. So we temporarily try adding swap (not a good long-term measure as it will kill the microSD flash card faster). Then it has to download tons of stuff, takes a really long time, and eventually runs out of disk space.
4. But hark! A recent Pydantic version is available as a system package! Same with PIL, which is also a long compile on this chip.

So, the consensus-solution is Python3.12, creating a venv, then editing pyenv.cfg to set include-system-site-packages = true. Then installing setuptools, Pydantic, and PIL system-wide. Finally, we install everything else with pip.

With this method, the normal ubiblio version can start up just fine! Honestly, this was less difficult than I thought it would be. I'll still keep this branch for any riscv64 specific changes I need to make in the future.

# If you actually want this

You can follow the vague instructions above, if you want.

However, I plan to image my working install with dd and compress it. Likely after the next release. This way you can just flash it to a 16GB microSD card, insert it into your board, and boot it up. So just give me a week or so.
