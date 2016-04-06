# SPL-T
A Python implementation of the iOS game SPL-T. This is a work in progress, it's not finished yet.

See [the game's website](http://simogo.com/work/spl-t/) for details. 

The eventual goal of this project is to find out the moves to play the perfect game of SPL-T, achieving the highest possible score. I plan to accomplish this either by:

1. Building a game tree that shows all possible moves from a given state, looking ahead only 3-4 moves. Then, choosing the optimal path at each turn
2. Using some kind of learning algorithm to train itself to play SPL-T. I'm not sure how realistic this is because of my lack of knowledge in this field. 

I'm working on this very intermittently, since it's pretty difficult logic-wise and I've got projects I want to work on more.

# TODO

- [ ] Game Logic
    - [x] Splitting tiles
    - [x] Forming point tiles
    - [x] Falling tiles
    - [ ] New tiles falling from ceiling
- [ ] Game interface
    - [ ] Leverage [Pythonista](http://omz-software.com/pythonista/index.html)'s `scene` module to build a touch interface for testing. 
- [ ] Game solution (either Minimax or Machine Learning)
    - [ ] Creating a method for assigning a numerical value to an arbitrary game state
    - [ ] Building game tree
    - [ ] Finding optimal moves
