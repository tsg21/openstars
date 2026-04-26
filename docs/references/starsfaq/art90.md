# Ground Combat calculations

*by: Ezequiel Martin Camara*

> Hi,
> I've been using invasion or ground combat extensively without really
> understanding the victory conditions.

You're not the only one...

The help file (2.7f dated August 17th) only tells you a few things about

> ground combat:

And the help file is outdated or simply wrong in several places, too!

> This leaves me with a question:-
> After taking into account the planetary defences, how do we know how many
> troops to unload?
> It would appear that an equal number of troops will fail.

No, it would not... the *attacker* has the advantage in Stars! gorund combat. A nice feature, I should say; the defense has lots of other advantages.

> Is there a more scientific way of knowing what to do or is there a rule of
> thumb I can apply?

I've always have thought that I would like the answer to all those questions. So I made a testbed and tried lots of ground combats. The way the game appears to calculate the result of ground combat is:

(attackers) = (attackers)*(1 - .75*(defense coverage))

(attack bonus) = 1.1*(1 + 0.5*(is attacker WM?)) (defense bonus) = 1 + (is defender IS?)

IF (attackers)*(attack bonus) > (defenders)*(defense bonus)

(owner) = (attacker race) (pop) = (attakers) - (defenders)*(defense bonus)/(attack bonus)

ELSE (owner) = (defender race) (pop) = (defenders) - (attackers)*(attack bonus)/(defense bonus)

Now I'll try to explain this pseudo-code:

(attackers) is the number of colonists you drop in an enemy planet, and (defenders) is the number of pop that planet has in the moment of the invasion. A couple of precisions there: if the invasion is a waypoint-zero task (that is, the freighter was already in the orbit of the planet) there's no growth involved, that is, the pop in the planet (and in the freighter for IS) is the same as last year. If the freighter invades the same year as it arrives to the orbit, there's growth before the invasion (people grow in the planet and in the freighters, then the calculations take place). And remember, the pop you see in your .m? file in enemy planets has a +/-20% error; to know exactly the pop in a planet, you have to see its owner's .m? file.

(defense coverage) in the formula is, well, the coverage given by the defenses, in a 0 to 1 scale (that is, if the .m? file says 85% the numbr to plug in the formula is (defense coverage)=0.85)

(is attacker WM?) and (is defender IS?) are =1 if they're true, =0 if they're false. So the bonuses end up as: (defense bonus)=1 unless the owner of the planet is IS, then (defense bonus)=2 (yeah, pretty high!). (attack bonus)=1.1 unless invader is WM, then (attack bonus)=1.65.

The bonuses tell you how much SD ("standard fighters") each fighter is worth. So 1 invader WM is worth 1.65 SD, 1 defender HE is worth 1 SD. Now the troop worth more SD keeps the planet, but the other race kills as many SD as it's worth. (that is, if the defender is worth 1000 SD and the invader 700 SD, the defender keeps the planet, but with only 300 SD left, whatever that means in terms of its own pop)

Now, I've tried a couple of triple invasions. I found it hard to make sense of the numbers... so I'll leave it for the more experienced testers. If someone wants to try, I have set up a testbed with three races (HE, IS and WM) so that each one has as much pop as it wants...

I hope that this will be of any help to someone (Matthias, will you include it in your calculator?) -- Real address is:

EMARTIN, at supernetsantander-dot-com

Ezequiel Martin Camara - Malaga - Spain
