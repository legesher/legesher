// FILE LOCATION: tree-sitter-python/grammars.js

const PREC = {
    // this resolves a conflict between the usage of ':' in a lambda vs in a
    // typed parameter. In the case of a lambda, we don't allow typed parameters.
    lambda: -2,
    typed_parameter: -1,
    conditional: -1,
    parenthesized_expression: 1,
    not: 1,
    compare: 2,
    or: 10,
    and: 11,
    bitwise_or: 12,
    bitwise_and: 13,
    xor: 14,
    shift: 15,
    plus: 16,
    times: 17,
    power: 18,
    unary: 19,
    call: 20
};

module.exports = grammar({
            name: "python",

            extras: ($) => [
                $.comment, /[\s\uFEFF\u2060\u200B]|\\\r?\n/
            ],

            externals: ($) => [
                $._newline,
                $._indent,
                $._dedent,
                $._string_start,
                $._string_content,
                $._string_end
            ],

            inline: ($) => [
                $._simple_statement, $._compound_statement, $.keyword_identifier
            ],

            word: ($) => $.identifier,

            rules: {
                module: ($) => repeat($._statement),

                _statement: ($) => choice($._simple_statements, $._compound_statement),

                // Simple statements

                _simple_statements: ($) => seq($._simple_statement, optional(repeat(seq($._semicolon, $._simple_statement))), optional($._semicolon), $._newline),

                _simple_statement: ($) => choice($.future_import_statement, $.import_statement, $.import_from_statement, $.print_statement, $.assert_statement, $.expression_statement, $.return_statement, $.delete_statement, $.raise_statement, $.pass_statement, $.break_statement, $.continue_statement, $.global_statement, $.nonlocal_statement, $.exec_statement),

                // KEYWORD: IMPORT
                import_statement: ($) => seq("{import}", $._import_list),

                import_prefix: ($) => repeat1("."),

                relative_import: ($) => seq($.import_prefix, optional($.dotted_name)),

                // KEYWORD: FROM / IMPORT
                future_import_statement: ($) => seq("{from}", "__future__", "{import}", $._import_list),

                import_from_statement: ($) => seq("{from}", choice($.relative_import, $.dotted_name), "{import}", choice($.wildcard_import, $._import_list, seq("(", $._import_list, ")"))),

                _import_list: ($) => seq(commaSep1(choice($.dotted_name, $.aliased_import)), optional(",")),

                // KEYWORD: AS
                aliased_import: ($) => seq($.dotted_name, "{as}", $.identifier),

                wildcard_import: ($) => "*",

                // KEYWORD: PRINT
                print_statement: ($) => choice(prec(1, seq(
                    // 'print',
                    "{print}", $.chevron, repeat(seq(",", $._expression)), optional(","))), prec(-1, seq(
                    // 'print',
                    "{print}", commaSep1($._expression), optional(",")))),

                chevron: ($) => seq(">>", $._expression),

                // KEYWORD: ASSERT
                assert_statement: ($) => seq("{assert}", $._expression, repeat(seq(",", $._expression))),

                expression_statement: ($) => choice($._expression, seq(commaSep1($._expression), optional(",")), $.assignment, $.augmented_assignment, $.yield),

                // KEYWORD: RETURN
                return_statement: ($) => seq("{return}", optional($.expression_list)),

                // KEYWORD: DEL
                delete_statement: ($) => seq("{del}", $.expression_list),

                // KEYWORD: RAISE
                raise_statement: ($) => seq("{raise}", optional($.expression_list), optional(seq("{from}", $._expression))),

                // KEYWORD: PASS / BREAK / CONTINUE
                pass_statement: ($) => prec.left("{pass}"),
                break_statement: ($) => prec.left("{break}"),
                continue_statement: ($) => prec.left("{continue}"),

                // Compount statements

                _compound_statement: ($) => choice($.if_statement, $.for_statement, $.while_statement, $.try_statement, $.with_statement, $.function_definition, $.class_definition, $.decorated_definition),

                // KEYWORD: IF
                if_statement: ($) => seq("{if}", $._expression, ":", $._suite, repeat($.elif_clause), optional($.else_clause)),

                // KEYWORD: ELIF
                elif_clause: ($) => seq("{elif}", $._expression, ":", $._suite),

                // KEYWORD: ELSE
                else_clause: ($) => seq("{else}", ":", $._suite),

                // KEYWORD: ASYNC / FOR / IN
                for_statement: ($) => seq(optional("{async}"), "{for}", $.variables, "{in}", $.expression_list, ":", $._suite, optional($.else_clause)),

                // KEYWORD: WHILE
                while_statement: ($) => seq("{while}", $._expression, ":", $._suite, optional($.else_clause)),

                // KEYWORD: TRY
                try_statement: ($) => seq("{try}", ":", $._suite, choice(seq(repeat1($.except_clause), optional($.else_clause), optional($.finally_clause)), $.finally_clause)),

                // KEYWORD: EXCEPT / AS
                except_clause: ($) => seq("{except}", optional(seq($._expression, optional(seq(choice("{as}", ","), $._expression)))), ":", $._suite),

                // KEYWORD: FINALLY
                finally_clause: ($) => seq("{finally}", ":", $._suite),

                // KEYWORD: ASYNC / WITH
                with_statement: ($) => seq(optional("{async}"), "{with}", commaSep1($.with_item), ":", $._suite),

                // KEYWORD: AS
                with_item: ($) => seq($._expression, optional(seq("{as}", $._expression))),

                // KEYWORD: ASYNC / DEF
                function_definition: ($) => seq(optional("{async}"), "{def}", $.identifier, $.parameters, optional(seq("->", $.type)), ":", $._suite),

                parameters: ($) => seq("(", optional($._parameters), ")"),

                lambda_parameters: ($) => $._parameters,

                _parameters: ($) => seq(commaSep1(choice($.identifier, $.keyword_identifier, $.tuple, $.typed_parameter, $.default_parameter, $.typed_default_parameter, $.list_splat, $.dictionary_splat)), optional(",")),

                default_parameter: ($) => seq(choice($.identifier, $.keyword_identifier), "=", $._expression),

                typed_default_parameter: ($) => prec(PREC.typed_parameter, seq(choice($.identifier, $.keyword_identifier), ":", $.type, "=", $._expression)),

                list_splat: ($) => seq("*", optional($._expression)),

                dictionary_splat: ($) => seq("*", "*", $._expression),

                // KEYWORD: GLOBAL
                global_statement: ($) => seq("{global}", commaSep1($.identifier)),

                // KEYWORD: NONLOCAL
                nonlocal_statement: ($) => seq("{nonlocal}", commaSep1($.identifier)),

                // KEYWORD: EXEC / IN
                exec_statement: ($) => seq("{exec}", $.string, optional(seq("{in}", commaSep1($._expression)))),

                // KEYWORD: CLASS
                class_definition: ($) => seq("{class}", $.identifier, optional($.argument_list), ":", $._suite),

                argument_list: ($) => seq("(", optional(commaSep1(choice($._expression, $.list_splat, $.dictionary_splat, $.keyword_argument))), optional(","), ")"),

                decorated_definition: ($) => seq(repeat1($.decorator), choice($.class_definition, $.function_definition)),

                decorator: ($) => seq("@", $.dotted_name, optional($.argument_list), $._newline),

                _suite: ($) => choice($._simple_statements, seq($._indent, repeat($._statement), $._dedent)),

                variables: ($) => seq(commaSep1($._primary_expression), optional(",")),

                expression_list: ($) => prec.right(seq(commaSep1($._expression), optional(","))),

                dotted_name: ($) => sep1($.identifier, "."),

                // Expressions
                _expression_within_for_in_clause: ($) => choice($._expression, alias($.lambda_within_for_in_clause, $.lambda)),

                _expression: ($) => choice($.comparison_operator, $.not_operator, $.boolean_operator, $.await, $.lambda, $._primary_expression, $.conditional_expression),

                _primary_expression: ($) => choice($.binary_operator, $.identifier, $.keyword_identifier, $.string, $.concatenated_string, $.integer, $.float, $.true, $.false, $.none, $.unary_operator, $.attribute, $.subscript, $.call, $.list, $.list_comprehension, $.dictionary, $.dictionary_comprehension, $.set, $.set_comprehension, $.tuple, $.parenthesized_expression, $.generator_expression, $.ellipsis),

                // KEYWORD: NOT
                not_operator: ($) => prec(PREC.not, seq("{not}", $._expression)),

                // KEYWORD: AND / OR
                boolean_operator: ($) => choice(prec.left(PREC.and, seq($._expression, "{and}", $._expression)), prec.left(PREC.or, seq($._expression, "{or}", $._expression))),

                binary_operator: ($) => choice(prec.left(PREC.plus, seq($._primary_expression, "+", $._primary_expression)), prec.left(PREC.plus, seq($._primary_expression, "-", $._primary_expression)), prec.left(PREC.times, seq($._primary_expression, "*", $._primary_expression)), prec.left(PREC.times, seq($._primary_expression, "@", $._primary_expression)), prec.left(PREC.times, seq($._primary_expression, "/", $._primary_expression)), prec.left(PREC.times, seq($._primary_expression, "%", $._primary_expression)), prec.left(PREC.times, seq($._primary_expression, "//", $._primary_expression)), prec.left(PREC.power, seq($._primary_expression, "**", $._primary_expression)), prec.left(PREC.bitwise_or, seq($._primary_expression, "|", $._primary_expression)), prec.left(PREC.bitwise_and, seq($._primary_expression, "&", $._primary_expression)), prec.left(PREC.xor, seq($._primary_expression, "^", $._primary_expression)), prec.left(PREC.shift, seq($._primary_expression, "<<", $._primary_expression)), prec.left(PREC.shift, seq($._primary_expression, ">>", $._primary_expression))),

                unary_operator: ($) => choice(prec(PREC.unary, seq("-", $._primary_expression)), prec(PREC.unary, seq("+", $._primary_expression)), prec(PREC.unary, seq("~", $._primary_expression))),

                // KEYWORD: NOT / IN / IS
                comparison_operator: ($) => prec.left(PREC.compare, seq($._primary_expression, repeat1(seq(choice("<", "<=", "==", "!=", ">=", ">", "<>", "{in}", seq("{not}", "{in}"), "{is}", seq("{is}", "{not}")), $._primary_expression)))),

                // KEYWORD: LAMBDA
                lambda: ($) => prec(PREC.lambda, seq("{lambda}", optional($.lambda_parameters), ":", $._expression)),

                lambda_within_for_in_clause: ($) => seq("{lambda}", optional($.lambda_parameters), ":", $._expression_within_for_in_clause),

                assignment: ($) => seq($.expression_list, choice(seq("=", $._right_hand_side), seq(":", $.type), seq(":", $.type, "=", $._right_hand_side))),

                augmented_assignment: ($) => seq($.expression_list, choice("+=", "-=", "*=", "/=", "@=", "//=", "%=", "**=", ">>=", "<<=", "&=", "^=", "|="), $._right_hand_side),

                _right_hand_side: ($) => choice($.expression_list, $.assignment, $.augmented_assignment, $.yield),

                // KEYWORD: YIELD / FROM
                yield: ($) => seq("{yield}", choice(seq("{from}", $._expression), optional($.expression_list))),

                attribute: ($) => seq($._primary_expression, ".", $.identifier),

                subscript: ($) => seq($._primary_expression, "[", commaSep1(choice($._expression, $.slice)), optional(","), "]"),

                slice: ($) => seq(optional($._expression), ":", optional($._expression), optional(seq(":", optional($._expression)))),

                ellipsis: ($) => "...",

                call: ($) => prec(PREC.call, seq($._primary_expression, choice($.generator_expression, $.argument_list))),

                typed_parameter: ($) => prec(PREC.typed_parameter, seq(choice($.identifier, $.list_splat, $.dictionary_splat), ":", $.type)),

                type: ($) => $._expression,

                keyword_argument: ($) => seq(choice($.identifier, $.keyword_identifier), "=", $._expression),

                // Literals

                list: ($) => seq("[", optional(commaSep1(choice($._expression, $.list_splat))), optional(","), "]"),

                _comprehension_body: ($) => seq($.for_in_clause, repeat(choice($.for_in_clause, $.if_clause))),

                list_comprehension: ($) => seq("[", $._expression, $._comprehension_body, "]"),

                dictionary: ($) => seq("{", optional(commaSep1(choice($.pair, $.dictionary_splat))), optional(","), "}"),

                dictionary_comprehension: ($) => seq("{", $.pair, $._comprehension_body, "}"),

                pair: ($) => seq($._expression, ":", $._expression),

                set: ($) => seq("{", commaSep1(choice($._expression, $.list_splat)), optional(","), "}"),

                set_comprehension: ($) => seq("{", $._expression, $._comprehension_body, "}"),

                parenthesized_expression: ($) => prec(PREC.parenthesized_expression, seq("(", choice($._expression, $.yield), ")")),

                tuple: ($) => seq("(", optional(commaSep1(choice($._expression, $.yield))), optional(","), ")"),

                generator_expression: ($) => seq("(", $._expression, $._comprehension_body, ")"),

                // KEYWORD: ASYNC / FOR / IN
                for_in_clause: ($) => seq(optional("{async}"), "{for}", $.variables, "{in}", commaSep1($._expression_within_for_in_clause), optional(",")),

                // KEYWORD: IF / ELSE
                if_clause: ($) => seq("{if}", $._expression),

                conditional_expression: ($) => prec.right(PREC.conditional, seq($._expression, "{if}", $._expression, "{else}", $._expression)),

                concatenated_string: ($) => seq($.string, repeat1($.string)),

                string: ($) => seq(alias($._string_start, '"'), repeat(choice($.interpolation, $.escape_sequence, $._string_content)), alias($._string_end, '"')),

                interpolation: ($) => seq("{", $._expression, optional($.type_conversion), "}"),

                escape_sequence: ($) => token(seq("\\", choice(/u[a-fA-F\d]{4}/, /U[a-fA-F\d]{8}/, /x[a-fA-F\d]{2}/, /o\d{3}/, /\r\n/, /[^uxo]/))),

                type_conversion: ($) => /![a-z]/,

                integer: ($) => token(choice(seq(choice("0x", "0X"), repeat1(/_?[A-Fa-f0-9]+/), optional(/[Ll]/)), seq(choice("0o", "0O"), repeat1(/_?[0-7]+/), optional(/[Ll]/)), seq(choice("0b", "0B"), repeat1(/_?[0-1]+/), optional(/[Ll]/)), seq(repeat1(/[0-9]+_?/), choice(optional(/[Ll]/), // long numbers
                                    optional(/[jJ]/) // complex numbers)))),

                                    float: ($) => token(seq(choice(seq(repeat(/[0-9]+_?/), ".", repeat(/[0-9]+_?/), optional(/[eE][\+-]?/), repeat(/[0-9]+_?/)), seq(repeat(/[0-9]+_?/), optional(/[eE][\+-]?/), repeat1(/[0-9]+_?/))), optional(choice(optional(/[Ll]/), // long numbers
                                                optional(/[jJ]/) // complex numbers)))),

                                                identifier: ($) => /[a-zA-Z_]\w*/,

                                                // KEYWORD: PRINT / EXEC
                                                // keyword_identifier: $ => alias(choice('{print}', '{exec}'), $.identifier),
                                                keyword_identifier: ($) => alias(choice("{print}", "{exec}"), $.identifier),

                                                // KEYWORD: TRUE / FALSE / NONE
                                                true: ($) => "{True}",
                                                false: ($) => "{False}",
                                                none: ($) => "{None}",

                                                // KEYWORD: AWAIT
                                                await :($) => prec(PREC.unary, seq("{await}", $._expression)),

                                                comment: ($) => token(seq("#", /.*/)),

                                                _semicolon: ($) => ";"
                                            }
                                        });

                                        function commaSep1(rule) {
                                            return sep1(rule, ",");
                                        }

                                        function sep1(rule, separator) {
                                            return seq(rule, repeat(seq(separator, rule)));
                                        }