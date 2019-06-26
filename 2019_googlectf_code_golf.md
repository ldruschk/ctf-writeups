# Code Golf
Part of the Google CTF 2019 (https://capturetheflag.withgoogle.com/)

Our task is to write a Haskell function `g :: [String] -> String` which takes a list of transparencies, i.e., Strings with characters and spaces and we have to stack them in such a way that no two characters overlap.

The maximum allowed length of the program (excluding imports) is 181 bytes.

These are the rules from the dask description:
```
For example, given the strings "ha  m" and "ck e":

If you overlay them:
    "ha  m" 
    "ck e" 

Shift them by an appropriate offset:
    "ha  m" 
      "ck e"

And combine them, you get "hackme".

For the data we're working with, the following rules seem to always hold:

1. The correct offset will never cause two characters to occupy the same column.
2. The correct offset will minimize the length of the final text after trimming
   leading and trailing spaces.
3. If there are multiple possible decryptions that follow the above rules, the
   lexicographically first one is correct.

To make matters worse, we only have a limited number of bytes in our payload:
your solution may contain at most 181 bytes of Haskell code.
```
We have the following modules which are already imported, meaning the import is not part of the character limit.
```
Prelude
Control.Applicative
Control.Arrow
Control.Monad
Data.Array
Data.Bits
Data.Bool
Data.Char
Data.Complex
Data.Dynamic
Data.Either
Data.Eq
Data.Fixed
Data.Function
Data.Graph
Data.Int
Data.Ix
Data.List
Data.Maybe
Data.Monoid
Data.Ord
Data.Ratio
Data.Tree
Data.Tuple
Data.Typeable
Data.Word
Debug.SimpleReflect
Text.Printf
ShowFun
```

## "Uncompressed" solution
```
import Data.List

-- Check if two strings can be merged
-- zip stops at the end of shorter string which is fine since the rest of the longer string can obviously be merged
canMerge :: String -> String -> Bool
canMerge x = all (\(x,y) -> x==' ' || y==' ') . zip x

-- Take two transparencies and overlay them (assumes no two characters overlap)
merge :: String -> String -> String
merge []     y      = y
merge x      []     = x
merge (x:xs) (y:ys) = (if x == ' ' then y else x):(merge xs ys)

-- strip (since Data.Text is not imported)
-- this is necessary in case we get e.g. "zz  " and "aa" as input, since otherwise
-- "zzaa" would be preferred because it is shorter than "aazz  " although the
-- latter would result in "aazz" with the same length and being first in
-- lexicographical order
strip :: String -> String
strip = stripL . stripR
stripL :: String -> String
stripL = dropWhile (==' ')
stripR :: String -> String
stripR = reverse . stripL . reverse

-- move each string to be inserted space by space to the right until it can be
-- merged, insert as far left as possible
shiftAndMerge :: [String] -> String
shiftAndMerge = foldl (\r -> merge r . until (canMerge r) (' ':)) ""

-- the g function works as follows
-- 1. strip the input strings
-- 2. take all permutations of the input strings and for each one, beginning with
--    an empty string, insert every transparency in that order as far left as
--    possible
-- 3. sort in lexicographical order
-- 4. (stable) sort by length, if two strings have the same length they are still
--    sorted in lexicographical order from before
-- 5. return the first string
g :: [String] -> String
g = head . sortOn length . sort . map shiftAndMerge . permutations
```

Not that Data.List is manually imported here so the script can easily be run on my local machine, however, it is not counted when determining the program length.

### Shortening `canMerge`
Starting with the uncompressed function:
```
-- Check if two strings can be merged
-- zip stops at the end of shorter string which is fine since the rest of the longer string can obviously be merged
canMerge :: String -> String -> Bool
canMerge x = all (\(x,y) -> x==' ' || y==' ') . zip x
```
Removing all comments, the signature and unnecessary whitespaces brings the function down to `44` bytes:
```
canMerge x=all(\(x,y)->x==' '||y==' ').zip x
```
Replacing the two comparisons with an elem call saves one additional byte (`43` bytes). Note that the whitespace after `elem` can not be removed.
```
canMerge x=all(\(x,y)->elem ' '[x,y]).zip x
```
We can save another `7` bytes (plus `7` bytes for the call to `canMerge`) bringing it down to `36` bytes by giving it a shorter name, however, the function will be turned into a lambda function later anyways.
```
c x=all(\(x,y)->elem ' '[x,y]).zip x
```

### Shortening `merge`
Starting with the uncompressed function:
```
-- Take two transparencies and overlay them (assumes no two characters overlap)
merge :: String -> String -> String
merge []     y      = y
merge x      []     = x
merge (x:xs) (y:ys) = (if x == ' ' then y else x):(merge xs ys)
```
As before, we start by simply removing "unnecessary stuff" and begin with `79` bytes, including two newlines:
```
merge[]y=y
merge x[]=x
merge(x:xs)(y:ys)=(if x==' 'then y else x):(merge xs ys)
```
We can remove the first two patterns by matching `merge x y` at the end, we will only get there if one of the strings is empty since otherwise the third pattern would be matched. We can simply concatenate `x` and `y` since the one of the strings is empty anyways, so the order does not matter. This brings it down to `71` bytes:
```
merge(x:xs)(y:ys)=(if x==' 'then y else x):(merge xs ys)
merge x y=x++y
```
The `if-then-else` can be replaced with a list built with list comprehension and a call to `last`. If `x==' '` is true, `y` will be added to the list and thus selected as the last element, otherwise the list contains only `x`. This saves `5` bytes bringing the function to `66` bytes.
```
merge(x:xs)(y:ys)=(last$x:[y|x==' ']):(merge xs ys)
merge x y=x++y
```
Obviously, another `12` bytes (plus `4` for the call to `merge`) can be saved by renaming the function (`54` bytes).
```
m(x:xs)(y:ys)=(last$x:[y|x==' ']):(m xs ys)
m x y=x++y
```
`xs` and `ys` can be renamed to `a` and `b`, saving `4` bytes (`50` bytes):
```
m(x:a)(y:b)=(last$x:[y|x==' ']):(m a b)
m x y=x++y
```
We will apply further "optimizations" later when looking at the whole program.
### Shortening `strip`
Starting with the uncompressed function:
```
-- strip (since Data.Text is not imported)
-- this is necessary in case we get e.g. "zz  " and "aa" as input, since otherwise "zzaa" would be preferred because it is shorter than "aazz  " although the latter would result in "aazz" with the same length and being first in lexicographical order
strip :: String -> String
strip = stripL . stripR
stripL :: String -> String
stripL = dropWhile (==' ')
stripR :: String -> String
stripR = reverse . stripL . reverse
```
By removing unnecessary stuff, renaming the functions to `s`,`t` and `u` and renaming `xs` to `x` we start with `44` bytes (`4` bytes are saved for the call to `strip`):
```
s=t.u
t=dropWhile(==' ')
u=reverse.t.reverse
```
Since we never need to use `stripL` and `stripR` separately, we can remove `u` (which was `stripR`) and instead replace `s` with `t.reverse.t.reverse` (saving `4` bytes => `40` bytes)
```
s=t.reverse.t.reverse
t=dropWhile(==' ')
```
Again, we will apply further optimizations later when looking at the whole program.
### Shortening `shiftAndMerge`
Since we renamed a few functions already the inital function looks different than in the first listing:
```
-- move each string to be inserted space by space to the right until it can be merged, insert as soon as possible
shiftAndMerge :: [String] -> String
shiftAndMerge = foldl (\r -> m r . until (c r) (' ':)) ""
```
Again, we remove unnecessary stuff and rename the function to `v`, which gives us `35` bytes:
```
v=foldl(\r->m r.until(c r)(' ':))""
```
We can save `1` byte by replacing `foldl` and the initial value `""` with `foldl1` which takes the first list element as initial value. However this means we can no longer work on empty lists (resulting in an error), but this case is not checked when submitting (`34` bytes):
```
v=foldl1(\r->m r.until(c r)(' ':))
```
Again, more optimizations will follow when looking at the complete program.
### Shortening `g`
The original:
```
g :: [String] -> String
g = head . sortOn length . sort . map v . permutations . map s
```
can be shortened to start with `50` bytes:
```
g=head.sortOn length.sort.map v.permutations.map s
```
We can replace `length` with `0<$`, which replaces all elements in the list with a `0`. This still works, since a shorter list with `0` is considered to be less than a longer list with `0`, i.e., `[0] < [0,0]`. This saves `2` bytes (`48` bytes):
```
g=head.sortOn(0<$).sort.map v.permutations.map s
```
## Shortening the whole the program
After combining everything we did earlier we end up with a program which is `212` bytes in size (reminder: the goal is at most `181` bytes). The values from the previous sections do not add up because we need to consider additional newlines now.

The changes we apply in this section were ignored before since they change multiple functions at once.

The current program is:
```
c x=all(\(x,y)->elem ' '[x,y]).zip x
m(x:a)(y:b)=(last$x:[y|x==' ']):(m a b)
m x y=x++y
s=t.reverse.t.reverse
t=dropWhile(==' ')
v=foldl1(\r->m r.until(c r)(' ':))
g=head.sortOn(0<$).sort.map v.permutations.map s
```
We can turn `c` and `v` into lambda functions, saving `8` and `3` bytes respectively (`201` bytes):
```
m(x:a)(y:b)=(last$x:[y|x==' ']):(m a b)
m x y=x++y
s=t.reverse.t.reverse
t=dropWhile(==' ')
g=head.sortOn(0<$).sort.map(foldl1(\r->m r.until(all(\(x,y)->elem ' '[x,y]).zip r)(' ':))).permutations.map s
```
Instead of defining `s=t.reverse.t.reverse`, which wastes a lot of bytes due to having `reverse` twice, we define `s=t.reverse` and replace the call to `s` with `s.s`.

This saves `10` bytes in the definition but costs `3` bytes when calling `(s.s)` since we need the parantheses, meaning we end up at `194` bytes:
```
m(x:a)(y:b)=(last$x:[y|x==' ']):(m a b)
m x y=x++y
s=t.reverse
t=dropWhile(==' ')
g=head.sortOn(0<$).sort.map(foldl1(\r->m r.until(all(\(x,y)->elem ' '[x,y]).zip r)(' ':))).permutations.map(s.s)
```
We now also no longer need the definition of `t` and can move it directly to the definition of `s`, saving `4` bytes (`190` bytes):
```
m(x:a)(y:b)=(last$x:[y|x==' ']):(m a b)
m x y=x++y
s=dropWhile(==' ').reverse
g=head.sortOn(0<$).sort.map(foldl1(\r->m r.until(all(\(x,y)->elem ' '[x,y]).zip r)(' ':))).permutations.map(s.s)
```
The function `m` can be turned into an inline operator named `!`, saving `4` bytes due to removing spaces in the definition, but costing `1` byte because the call to `m r` becomes `(!r)` (`187` bytes):
```
(x:a)!(y:b)=(last$x:[y|x==' ']):(a!b)
x!y=x++y
s=dropWhile(==' ').reverse
g=head.sortOn(0<$).sort.map(foldl1(\r->(!r).until(all(\(x,y)->elem ' '[x,y]).zip r)(' ':))).permutations.map(s.s)
```
The space character `' '` is used four times and costs `3` bytes each. Since none of the occurrences are in a pattern, we can introduce a variable `w=' '` which costs `6` bytes including the newline, but each of the occurrences now only costs `1` byte, saving `2` bytes overall (`185` bytes):
```
w=' '
(x:a)!(y:b)=(last$x:[y|x==w]):(a!b)
x!y=x++y
s=dropWhile(==w).reverse
g=head.sortOn(0<$).sort.map(foldl1(\r->(!r).until(all(\(x,y)->elem w[x,y]).zip r)(w:))).permutations.map(s.s)
```
## Final Solution (`151` bytes)
At this point we were stuck four bytes short of the goal. However, as it turned out the checker service does not actually supply strings with leading or trailing spaces (woopsie `¯\_(ツ)_/¯`), so we can throw the whole stripping logic away saving `34` bytes at once (note that we also replace `w` with `' '` again, which ends up being +/-`0` bytes, but looks nicer) for a total of `151` bytes:
```
(x:a)!(y:b)=(last$x:[y|x==' ']):(a!b)
x!y=x++y
g=head.sortOn(0<$).sort.map(foldl1(\r->(!r).until(all(\(x,y)->elem ' '[x,y]).zip r)(' ':))).permutations
```

This yields the flag `CTF{since-brevity-is-the-soul-of-wit-I-will-be-brief}` when submitted. Yay!

It should however be noted that the solution does not yield correct results when called with e.g. `["z ","a"]` and it crashes when called with `[]`. The shortest solution we have that covers all edge cases is `186` bytes in length (since we need to replace `foldl1` with `foldl` and `""` again). If you have any idea how to get rid of the remaining `5` bytes, please let me know.
```
w=' '
(x:a)!(y:b)=(last$x:[y|x==w]):(a!b)
x!y=x++y
u=reverse.dropWhile(==w)
g=head.sortOn(0<$).sort.map(foldl(\r->(!r).until(all(\(x,y)->elem w[x,y]).zip r)(w:))"").permutations.map(u.u)
```

## Update (2019-06-26)
As pointed out by @mcpower in [their writeup](https://github.com/mcpower/ctf-writeups/blob/master/2019-gctf-code-golf.md) and in [issue #1](https://github.com/ldruschk/ctf-writeups/issues/1), our solution fails to handle yet another special case, namely e.g. `["a  a","b"]`, which should yield `"a ba"` according to the rules but yields `"ab a"` with our solution.

But they also came up with a better variant of the `!` function, which simply returns `max` of the first two inputs. This works since any printable character will always be greater than `' '`. Similarly, they also managed to shorten our `all(\(x,y)->elem w[x,y]).zip r` even further. This brings the "wrong" and "somewhat right" solutions down to `132` bytes and `168` bytes respectively.

However, while one would expect the "somewhat right" solution to be accepted as well (since even the "wrong" solution was accepted), the only difference being the stripping of leading/trailing spaces which the second rule requires, it actually causes the checker to fail.

@mcpower also tested whether the strings should be trimmed when determining the length and ordering them but not when returning them, but this failed as well.

At this point it's probably best to wait for Google to release the source code of the checker, as has been done for their CTFs in the past, but the second rule seems to be either misleading or there is something wrong with the checker.

## Acknowledgements
Thanks to the authors of all the useful replies in this StackExchange thread: https://codegolf.stackexchange.com/questions/19255/tips-for-golfing-in-haskell