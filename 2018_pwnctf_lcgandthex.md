# LCG and the X (worth 250+205 points)
Part of the P.W.N. University CTF 2018 (https://uni.hctf.fun/pages/home/)

```
CHECK OUT THIS NEW ON CAPUS FANCLUB!!!
The LCG and the X FANCLUB
```

The description includes a link to the service with the following description:
```
Hello!
This is the website for our on-campus fanclub of the band LCG and the X!
Everyone can signup for the club to:

   Get the latest LCG news
   Communicate with other fans
   Save secret messages prefixed with "flag{" (which is always handy...)
```
Saving secret messages prefixed with "flag{" definitely sounds like something we want.

When signing up we can provide some info (name, address, country and phone). This shows us a new page with an (auto-incremented) user number and a "random" numerical password that we can use to login as well as a personal password recovery token in the form of a 128x128 black&white bitmap (see below).

![bitmap of the recovery token for user 42]("./2018_pwnctf_lcgandthex_1.bmp")

The News we can find on the website include:
```
[...]
I also just signed up to make sure the signup process works.
Then I created a secret flag, which worked as well!
[...]
Because of the new data protection laws in europe I decided to temporarily disable the secret flag storage... I hope I can bring it back up soon...
```
When accessing the flag storage we get the message:
```
The Flag storage is currently disabled, only flags that you already have submitted will be shown here.
```
So we know that the flag has been placed by the creator who most likely has the user number 1. If we could login as that user, we could see the flag.

Revisiting the registration site we noticed that the password recovery token hat a URL in the format of `http://.../42.bmp` where `42` was our (actual) user id (lucky, right?). Obviously we now also had access to the password recovery token of the first user (see below), but one question remained: How do we use this token?

![bitmap of the recovery token for user 1]("./2018_pwnctf_lcgandthex_42.bmp")

The site offers no functionality to recover a password by uploading a token, so we assumed that all relevant information is encoded in the bitmap. By creating some more accounts with the same inputs for name etc. we realized that the tokens appeared to be completely randomized each time, with the user number having no immediately visible imapct.

We played around a bit with the bitmap and tried interpreting it as ASCII encoded text, but that failed. We then noticed that at least the first four bits in each line were black, so we assumed this could be 128-bit binary numbers in each row with the four most significant bits being zero.

We came up with a quick python script to parse the image and output the 128 numbers.
```
import math
import os
import sys
import imageio

if len(sys.argv) != 2:
    print("Usage: %s file.bmp" % sys.argv[0])
    sys.exit(1)

filename = sys.argv[1]

image = imageio.imread(filename)
out = 0
for line in image:
    tmp = 0
    for x in range(len(line)):
        tmp <<= 1
        tmp |= 1 if line[x] == 255 else 0
    print("% 40d" % tmp)
```

The output for user 42 is:
```
13285128405728512840572851284044
7321782569713832870711499107358401786
1589124231055101792582259868857807391
[124 more numbers]
6133478240011003618640769383369411060
```

The password for user 42 is `6429760596071210556499524060198881378`, which unfortunately (but not unsurprisingly) was not among the output numbers.

To verify that these numbers actually make sense (you could interpret anything as binary encoded numbers even if it was not intended to be) we tried comparing the numbers of two sequential users and luckily noticed that the first numbers, when subtracted, showed a difference of `313373133731337313373133731337`. That was too good to be coincidence, so we were definitely on the right track.

## LCG and the multiplier, addend and modulo
If you try to make sense of the challenge title you inevitably end up on the Wikipedia page about `Linear Congruential Generator`s. This is a simple kind of (not cryptographically secure) random number generators. They have the general form of `X(n+1) = (a*X(n) + c) mod m` where `a` is the multiplier, `c` is the addend and `m` is the modulo. Together with the seed `X(0)` they uniquely define the behavior of the generator.

However, we just have a bunch of outputs but don't know anything about `a`, `c` and `m`. Luckily these generators are extremely easy to break if you have three complete states, i.e., three sequential and unmodified outputs. And even better, you don't actually have to understand how this works since smart people already did the work and posted their python scripts online (See: https://tailcall.net/blog/cracking-randomness-lcgs/ ). The details aren't covered here since the linked blog post explains it quite well, so go read it if you are interested.

Otherwise just run the included scripts to get the following values:
```
m = 16285270385112413720426683811263350667
a = 313373133731337313373133731337
c = 123456789012345678901234567890
```

At this point we only have to guess what output of the RNG is the password (Spoiler: it's the 129th), but we can do this easily by playing around with the token of a user which we know the password of. So just take the last number `x127` from the recovery image and calculate `((a * x127) + c) % m` to get the password.

To recover the password of the first user either download their recovery image and start from the last number or, alternatively, take the initial seed of your user with the known number (e.g. `13285128405728512840572851284044` for user 42) and subtract `41*313373133731337313373133731337` to get the initial seed of the first user. Now you can just calculate 128 steps of the RNG to get the same password.

With the password `6160325624856057770563639672902954513` we could then login as the first to retrieve the flag `flag{https://www.youtube.com/watch?v=NvS351QKFV4#Y0L0SW4G}`.
