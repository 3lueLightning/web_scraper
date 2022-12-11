All items in the products page are organised in a hierarchical category system
(in 3 levels going from more general to more specific)  
This XPATH captures the most specific level 'third-level', except 'Ver Todos'.
'Ver Todos' was excluded because it encompasses all the product in a category level 2.
It would be a more convenient way of accessing all items if only it was present everywhere
however only some level 2 categories have it. So to avoid scraping all the items of a given
level 2 category twice, we exclude it.  
ex class: 
```html
'header__submenu-third-level-sitemap qa-header__submenu-third-level--'
```
```html
//a[contains(@class, 'submenu-third-level') and not(contains(text(), 'Ver Todos'))]
```

However, we don't want all the class level 2 items as we are only interested in electronic items
So we restrict to:
* large home appliances: 'Grandes Eletrodomésticos'
* small home appliances: 'Pequenos Eletrodomésticos'
* TVs, video and sound: 'TV, Vídeo e Som'
* IT and acessories: 'Informática e Acessórios'  
```html
//div[contains(@class, 'submenu-second-level') and contains(/div/span/text(), 'Eletrodomésticos')]  
```
However, it was actually sufficient only to use:
```html
//div[div/span[contains(text(), 'Eletrodomésticos') or contains(text(), 'TV, Vídeo e Som') or contains(text(), 'Informática e Acessórios')]]
```

Now, we want all the categories level 3 that are on the unordered list (ul) which is the
only sibling of the category selected above, which is indicated by `following-sibling::ul`  
So the final XPATH becomes:
```html
//div[div/span[contains(text(), 'Eletrodomésticos') or contains(text(), 'TV, Vídeo e Som') or contains(text(), 'Informática e Acessórios')]]//following-sibling::ul//a[contains(@class, 'submenu-third-level') and not(contains(text(), 'Ver Todos')) and not(contains(text(), 'Ajuda-me a escolher'))]
```