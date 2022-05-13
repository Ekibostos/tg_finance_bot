create table budget(
    codename varchar(255) primary key,
    daily_limit integer
);

create table category(
    codename varchar(255) primary key,
    name varchar(255),
    is_base_expense boolean,
    aliases text
);

create table expense(
    id integer primary key,
    amount integer,
    created datetime,
    category_codename integer,
    raw_text text,
    FOREIGN KEY(category_codename) REFERENCES category(codename)
);

insert into category (codename, name, is_base_expense, aliases)
values
    ("products", "продукты", true, "еда"),
    ("coffee", "кофе", false, ""),
    ("dinner", "обед", true, "столовая, ланч, бизнес-ланч, бизнес ланч"),
    ("apartment", "квартира", true, "аренда, коммуналка, аренда квартиры"),
    ("beer", "пиво", false, "чипсы, пивасик, вино"),
    ("cafe", "кафе", false, "ресторан, рест, бар, грот, грот бар, гротбар"),
    ("transport", "общ. транспорт", false, "метро, автобус, metro"),
    ("for the home", "для дома", true, "порошок, стиральный порошок, мыло, шампунь, пена, пена для ванны, зубная паста, паста, средство, средство для мытья посуды, губки"),
    ("taxi", "такси", false, "яндекс такси, yandex taxi"),
    ("phone", "телефон", false, "ростелеком, связь, билайн"),
    ("books", "книги", false, "литература, литра, лит-ра"),
    ("internet", "интернет", false, "инет, inet"),
    ("subscriptions", "подписки", false, "подписка"),
    ("other", "прочее", false, "");

insert into budget(codename, daily_limit) values ('base', 800);
