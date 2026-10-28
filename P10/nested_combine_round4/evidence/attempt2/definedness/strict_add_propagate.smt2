; benchmark generated from python API
(set-info :status unknown)
(declare-fun b () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun p () (_ BitVec 1))
(assert
 (let (($x55 (and (distinct ((_ extract 7 0) (bvadd ((_ extract 7 0) a) ((_ extract 7 0) b))) (bvadd ((_ extract 7 0) ((_ extract 7 0) a)) ((_ extract 7 0) ((_ extract 7 0) b)))) true)))
(let (($x9 (and (distinct p (_ bv0 1)) true)))
(let (($x10 (and true true $x9)))
(let (($x21 (and $x10 $x10)))
(let (($x22 (and (and true true) true $x9)))
(or (and (distinct $x22 $x21) true) (and $x22 $x21 $x55))))))))
(check-sat)
