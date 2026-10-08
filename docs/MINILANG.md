# MiniLang

Types `int`, `float`, `bool`. Braces are mandatory on every `if`/`else`/`while` body. `//` comments.

Tokens: KEYWORD (`int float bool if else while print true false`), IDENTIFIER `[a-zA-Z_][a-zA-Z0-9_]*`, INT_LIT `[0-9]+`,
FLOAT_LIT `[0-9]+\.[0-9]+`, OPERATOR (`+ - * / = == != < <= > >= && || !`), DELIMITER (`( ) { } ;`). Longest match.

```text
program    -> stmt_list
stmt_list  -> stmt_list stmt | stmt
stmt       -> decl | assign | if_stmt | while_stmt | print_stmt | block
decl       -> type ID ';' | type ID '=' expr ';'
type       -> 'int' | 'float' | 'bool'
assign     -> ID '=' expr ';'
if_stmt    -> 'if' '(' expr ')' block | 'if' '(' expr ')' block 'else' block
while_stmt -> 'while' '(' expr ')' block
print_stmt -> 'print' '(' expr ')' ';'
block      -> '{' stmt_list '}'
expr       -> expr '||' and_e | and_e
and_e      -> and_e '&&' rel | rel
rel        -> add RELOP add | add
add        -> add '+' term | add '-' term | term
term       -> term '*' unary | term '/' unary | unary
unary      -> '-' unary | '!' unary | primary
primary    -> INT_LIT | FLOAT_LIT | 'true' | 'false' | ID | '(' expr ')'
```

Types: arithmetic on int/float (any float gives float); relational on numbers gives bool, `==`/`!=` also on bool pairs;
`&& || !` need bool; assignment needs an exact match or int into float; `if`/`while` conditions must be bool.
Scopes: each `{ }` opens `block_1`, `block_2`, ... under `global`; declare before use; no redeclaration in a scope; shadowing allowed.
Reading a declared-but-never-assigned variable is a warning.
